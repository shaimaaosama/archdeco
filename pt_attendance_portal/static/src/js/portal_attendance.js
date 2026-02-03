/** @odoo-module */
// Cache bust: Simplified animations and fixed cooldown timer - v1.2

import PublicWidget from "@web/legacy/js/public/public_widget";
import { debounce } from "@bus/workers/websocket_worker_utils";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { Deferred } from "@web/core/utils/concurrency";
import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog";

export const PortalAttendanceHome = PublicWidget.Widget.extend({
    selector: '.o_portal_my_home',
    events: {
        "click .o_hr_attendance_sign_in_out_icon": "_onClickInOut",
    },

    start: function () {
        var def = this._super.apply(this, arguments);
        return def;
    },

    _onClickInOut: function (ev) {
        ev.preventDefault();
        window.location.href = '/my/hr_attendances/create_new';
    },
});

export const PortalAttendanceHomeControllers = PublicWidget.Widget.extend({
    selector: '#wrapwrap:has(.p_o_hr_attendance_kiosk_mode_container)',
    cssLibs: [],
    jsLibs: [],
    events: {
        "click .p_o_hr_attendance_sign_in_out_icon": debounce(function (e) {
            // Prevent multiple clicks during processing
            if (this.isProcessingAttendance) {
                console.log("Attendance already being processed, ignoring click");
                return;
            }
            this.update_attendance();
        }, 200, true),
        'click .p_o_gmap_kisok_toggle': '_toggle_olmap',
        'click .p_o_gip_kisok_toggle': '_toggle_gip',
        'click .p_o_glocation_kisok_toggle': '_toggle_glocation',
        'change .p_o_attendance_reasons': '_on_change_reason',
    },
    custom_events: {},
    
    init() {
        this._super(...arguments);
        this.dialog = this.bindService("dialog");
        this.notificationService = this.bindService("notification");

        // Cache for geofence data
        this._geofenceCache = {};

        // Initialize state variables
        const employeeInputEl = document.querySelector('input#employee_input');
        this.employee_id = employeeInputEl ? (employeeInputEl.dataset.employeeId || employeeInputEl.getAttribute('data-employee_id')) : false;
        this.company_id = employeeInputEl ? (employeeInputEl.dataset.companyId || employeeInputEl.getAttribute('data-company_id')) : false;
        this.user_id = employeeInputEl ? (employeeInputEl.dataset.userId || employeeInputEl.getAttribute('data-user_id')) : false;

        // Initialize attendance processing state
        this.isProcessingAttendance = false;

        // Disable button by default
        this._disableButton();
        
        // Check cooldown after page loads
        setTimeout(() => {
            this._checkCooldown();
        }, 1000);

        // Feature flags - using consistent naming
        const employeeInput = employeeInputEl;
        this.hr_attendance_geolocation_p = employeeInput ? (employeeInput.dataset.hrAttendanceGeolocationP || employeeInput.getAttribute('data-hr_attendance_geolocation_p')) ? true : false : false;
        this.hr_attendance_geofence_p = employeeInput ? (employeeInput.dataset.hrAttendanceGeofenceP || employeeInput.getAttribute('data-hr_attendance_geofence_p')) ? true : false : false;
        this.hr_attendance_face_recognition_p = employeeInput ? (employeeInput.dataset.hrAttendanceFaceRecognitionP || employeeInput.getAttribute('data-hr_attendance_face_recognition_p')) ? true : false : false;
        this.hr_attendance_ip_p = employeeInput ? (employeeInput.dataset.hrAttendanceIpP || employeeInput.getAttribute('data-hr_attendance_ip_p')) ? true : false : false;
        this.hr_attendance_reason_p = employeeInput ? (employeeInput.dataset.hrAttendanceReasonP || employeeInput.getAttribute('data-hr_attendance_reason_p')) ? true : false : false;
        
        console.log("Feature flags loaded:", {
            geolocation: this.hr_attendance_geolocation_p,
            geofence: this.hr_attendance_geofence_p,
            face_recognition: this.hr_attendance_face_recognition_p,
            ip: this.hr_attendance_ip_p,
            reason: this.hr_attendance_reason_p
        });
    },
    
    willStart: async function () {
        const self = this;
        const def = this._super.apply(this, arguments);
        
        // Create promises for async operations
        const promises = [def];
        
        // Get employee data - ensure it's loaded before proceeding
        const employeePromise = rpc('/pt_attendance_portal/search_read/get_employee_data', {
            'employee_id': parseInt(this.employee_id),
        }).then(function (res) {
            self.employee = res.length && res[0];
            console.log("Employee data loaded:", self.employee);
            
            // Re-read feature flags from employee data if available (more reliable than data attributes)
            if (self.employee && self.employee.company_id) {
                // Try to get company settings if available
                const companyId = Array.isArray(self.employee.company_id) ? self.employee.company_id[0] : self.employee.company_id;
                console.log("Company ID from employee:", companyId);
            }
            
            // Update UI immediately after employee data is loaded
            if (self.employee) {
                self._updateAttendanceUI();
                
                // If map is already initialized, load geofence zones now
                if (self.olmap && self.vectorSource && self.hr_attendance_geofence_p) {
                    console.log("Employee data loaded, loading geofence zones on map...");
                    self._loadGeofenceZonesOnMap().then(() => {
                        if (self.olmap && self.vectorSource && self.vectorSource.getFeatures().length > 0) {
                            setTimeout(() => {
                                try {
                                    const extent = self.vectorSource.getExtent();
                                    if (extent && !isNaN(extent[0]) && !isNaN(extent[1])) {
                                        self.olmap.getView().fit(extent, {
                                            padding: [20, 20, 20, 20],  // Minimal padding for close fit
                                            maxZoom: 18
                                            // No minZoom - let it fit based on actual area size
                                        });
                                        
                                        self.olmap.updateSize();
                                        console.log("Map view updated after geofence zones loaded, zoom:", self.olmap.getView().getZoom());
                                    }
                                } catch (fitError) {
                                    console.error("Error fitting map view:", fitError);
                                }
                            }, 300);
                        }
                    });
                }
            }
        }).catch(function(error) {
            console.error("Failed to get employee data:", error);
            // Still try to update UI even if employee data fails
            self._updateAttendanceUI();
        });
        
        promises.push(employeePromise);
        
        // Check if employee has face descriptors if face recognition is enabled
        if (this.hr_attendance_face_recognition_p) {
            const faceDescriptorPromise = rpc('/pt_attendance_portal/check_employee_face_descriptors', {
                'employee_id': parseInt(this.employee_id),
            }).then(function (res) {
                self.employee_has_face_descriptors = res.has_face_descriptors;
                self.employee_face_count = res.face_count;
                console.log("Employee face descriptors check:", res);
            }).catch(function(error) {
                console.error("Failed to check employee face descriptors:", error);
                self.employee_has_face_descriptors = false;
                self.employee_face_count = 0;
            });
            
            promises.push(faceDescriptorPromise);
            
            // Only load face recognition models if employee has descriptors
            if (self.employee_has_face_descriptors) {
                this.load_label = new Deferred();
                const facePromise = this.load_models().catch(function(error) {
                    console.error("Failed to load face recognition models:", error);
                });
                promises.push(facePromise);
            }
        }
        
        return Promise.all(promises);
    },
    
    start: function () {
        const self = this;
        
        return this._super.apply(this, arguments).then(function () {
            // Temporarily disable buttons to prevent multiple clicks
            const signOutIcons = document.querySelectorAll("a.hr_attendance_sign_out_icon");
            const signInIcons = document.querySelectorAll("a.hr_attendance_sign_in_icon");
            signOutIcons.forEach(el => el.style.pointerEvents = 'none');
            signInIcons.forEach(el => el.style.pointerEvents = 'none');

            // Initialize geofence if enabled
            self.def_geofence = new Deferred();
            console.log("Checking geofence feature flag:", self.hr_attendance_geofence_p);
            if (self.hr_attendance_geofence_p) {
                console.log("Geofence is enabled, showing interface");
                // Show geofence container immediately - remove inline style to override template default
                const geofenceContainer = self.$('.p_o_gmap_kisok_container');
                if (geofenceContainer.length) {
                    geofenceContainer[0].style.display = 'block';
                    console.log("Geofence container shown, element:", geofenceContainer[0]);
                } else {
                    console.error("Geofence container not found in DOM");
                }
                // Always initialize map to show geofence zones, even on HTTP
                // (validation will still require HTTPS)
                self._initMap().catch(error => {
                    console.error("Error initializing map:", error);
                    self.def_geofence.resolve();
                });
            } 
            else {     
                console.log("Geofence is disabled, hiding interface");
                const geofenceContainer = self.$('.p_o_gmap_kisok_container');
                if (geofenceContainer.length) {
                    geofenceContainer[0].style.display = 'none';
                }
                self.def_geofence.resolve();
            }

            // Initialize IP address tracking if enabled
            self.def_ipaddress = new Deferred();
            console.log("Checking IP address feature flag:", self.hr_attendance_ip_p);
            if (self.hr_attendance_ip_p) {
                console.log("IP address tracking is enabled, showing interface");
                // Show IP address container immediately - remove inline style to override template default
                const ipContainer = self.$('.p_o_gip_kisok_container');
                if (ipContainer.length) {
                    ipContainer[0].style.display = 'block';
                    console.log("IP address container shown, element:", ipContainer[0]);
                } else {
                    console.error("IP address container not found in DOM");
                }
                self._getUserIP();
            } else {
                console.log("IP address tracking is disabled, hiding interface");
                const ipContainer = self.$('.p_o_gip_kisok_container');
                if (ipContainer.length) {
                    ipContainer[0].style.display = 'none';
                }
                self.def_ipaddress.resolve();
            }
            
            // Initialize geolocation if enabled
            self.def_geolocation = new Deferred();
            console.log("Checking geolocation feature flag:", self.hr_attendance_geolocation_p);
            if (self.hr_attendance_geolocation_p) {
                console.log("Geolocation is enabled, showing interface");
                // Show geolocation container immediately - remove inline style to override template default
                const geolocationContainer = self.$('.p_o_glocation_kisok_container');
                if (geolocationContainer.length) {
                    geolocationContainer[0].style.display = 'block';
                    console.log("Geolocation container shown, element:", geolocationContainer[0]);
                } else {
                    console.error("Geolocation container not found in DOM");
                }
                if (window.location.protocol === 'https:') {
                    self._getGeolocation();
                } else {
                    console.warn("Geolocation requires HTTPS, but showing interface anyway");
                    // Even on HTTP, try to get geolocation (some browsers allow it)
                    self._getGeolocation().catch(err => {
                        console.warn("Geolocation failed on HTTP:", err);
                        // Show a message that geolocation requires HTTPS
                        self.latitude = null;
                        self.longitude = null;
                        self.locationName = 'Geolocation requires HTTPS connection';
                        self._updateGeolocationDisplay();
                    });
                    self.def_geolocation.resolve();
                }
            } 
            else {
                console.log("Geolocation is disabled, hiding interface");
                const geolocationContainer = self.$('.p_o_glocation_kisok_container');
                if (geolocationContainer.length) {
                    geolocationContainer[0].style.display = 'none';
                }
                self.def_geolocation.resolve();
            }

            // Re-enable buttons after a delay
            setTimeout(function() {
                $("a.hr_attendance_sign_out_icon").css('pointer-events', '');
                $("a.hr_attendance_sign_in_icon").css('pointer-events', '');
            }, 1000);
            
            if (self.hr_attendance_reason_p){
                self.$('.p_o_attendance_reason').css('display', 'block');
            }

            self._updateAttendanceUI();
        });
    },
    
    _updateAttendanceUI: function() {
        const self = this;
        let hrs_today = "00:00";
        
        console.log("Updating attendance UI, employee:", self.employee);
        
        if (self.employee && self.employee.hours_today !== undefined) {
            hrs_today = self.convertNumToTime(self.employee.hours_today);
        }
        
        if (self.employee && self.employee.attendance_state === 'checked_in') {
            console.log("Employee is checked in, showing check out button");
            $("a.hr_attendance_sign_out_icon").show();
            $("a.hr_attendance_sign_in_icon").hide();
            
            $(".hr_attendance_sign_out_text").show();
            $(".hr_attendance_sign_in_text").hide();
            
            const hoursElement = $("h4.hours_today");
            if (hoursElement.length) {
                hoursElement.removeClass('d-none').find('span')[0].innerText = hrs_today;
            }
        } 
        else if (self.employee && self.employee.attendance_state === 'checked_out') {
            console.log("Employee is checked out, showing check in button");
            $("a.hr_attendance_sign_out_icon").hide();
            $("a.hr_attendance_sign_in_icon").show();
            
            $(".hr_attendance_sign_out_text").hide();
            $(".hr_attendance_sign_in_text").show();
            
            const hoursElement = $("h4.hours_today");
            if (hoursElement.length) {
                hoursElement.removeClass('d-none').find('span')[0].innerText = hrs_today;
            }
        } else {
            // Default: show check in button if employee state is unknown
            console.log("Employee state unknown, defaulting to check in");
            $("a.hr_attendance_sign_out_icon").hide();
            $("a.hr_attendance_sign_in_icon").show();
            
            $(".hr_attendance_sign_out_text").hide();
            $(".hr_attendance_sign_in_text").show();
        }
    },
    
    _loadFaceapi() {
        const self = this;
        return new Promise((resolve, reject) => {
            if ("faceapi" in window && window.faceapi) {
                resolve();
                return;
            }
            
            (function (w, d, s, g, js, fjs) {
                g = w.faceapi || (w.faceapi = {});
                g.faceapi = { q: [], ready: function (cb) { this.q.push(cb); } };
                js = d.createElement(s); 
                fjs = d.getElementsByTagName(s)[0];
                js.src = window.origin + '/pt_attendance_portal/static/src/lib/faceapi/source/face-api.js';
                js.onload = function () {
                    console.log("Face API loaded");
                    resolve();
                };
                js.onerror = function() {
                    console.error("Failed to load Face API");
                    reject(new Error("Failed to load Face API"));
                };
                fjs.parentNode.insertBefore(js, fjs);
            }(window, document, 'script'));
        });
    },
    
    load_models() {
        const self = this;
        
        // Initialize load_label if it doesn't exist
        if (!self.load_label) {
            self.load_label = new Deferred();
        }
        
        // First load face-api.js if not already loaded
        return self._loadFaceapi().then(() => {
            // Check if faceapi is available
            if (typeof faceapi === 'undefined') {
                console.error("Face API not loaded");
                return Promise.reject(new Error("Face API not loaded"));
            }
            
            return Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
                faceapi.nets.faceLandmark68Net.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
                faceapi.nets.faceLandmark68TinyNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
                faceapi.nets.faceRecognitionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
                faceapi.nets.faceExpressionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            ]).then(function() {
                if (self.load_label) {
                    self.load_label.resolve();
                }
                return self.loadLabeledImages();
            });
        });
    },
    
    async loadLabeledImages() {
        const self = this;
        try {
            const data = await rpc('/pt_attendance_portal/loadLabeledImages/');
            self.labeledFaceDescriptors = await Promise.all(
                data.map((item) => {
                    const descriptors = [];
                    for (let i = 0; i < item.descriptors.length; i++) {
                        if (item.descriptors[i].length !== 0) {
                            const desc = new Uint8Array([...window.atob(item.descriptors[i])].map(d => d.charCodeAt(0))).buffer;
                            if (desc.byteLength > 0) {
                                descriptors.push(new Float32Array(desc));
                            }
                        }
                    }
                    return new faceapi.LabeledFaceDescriptors(item.label.toString(), descriptors);
                })
            );
            return self.labeledFaceDescriptors;
        } catch (error) {
            console.error("Error loading labeled images:", error);
            throw error;
        }
    },
    
    _getGeolocation: function () {
        const self = this;
        
        if (!navigator.geolocation) {
            console.warn("Geolocation is not supported by this browser.");
            self.$('.p_o_glocation_kisok_container').css('display', '');
            self.def_geolocation.resolve();
            return Promise.resolve(null);
        }
        
        self.geolocationPromise = new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    try {
                        self.latitude = latitude;
                        self.longitude = longitude;
                        self.$('.p_o_glocation_kisok_container').css('display', '');
                        
                        // Get location name via reverse geocoding (don't fail if this fails)
                        try {
                            await self._getLocationName(latitude, longitude);
                        } catch (nameError) {
                            console.warn("Could not get location name:", nameError);
                        }
                        
                        // Update the display
                        self._updateGeolocationDisplay();
                        
                        // Auto-expand if we have coordinates
                        self._autoExpandGeolocation();
                        
                        self.def_geolocation.resolve();
                        resolve({latitude, longitude});
                    } catch (error) {
                        console.error("Error processing geolocation:", error);
                        self.def_geolocation.resolve();
                        resolve(null); // Resolve with null instead of rejecting
                    }
                },
                async err => {
                    // Handle different error types gracefully
                    let errorMessage = "Unknown geolocation error";
                    switch(err.code) {
                        case err.TIMEOUT:
                            errorMessage = "Geolocation request timed out. Please check your location settings or try again.";
                            console.warn("Geolocation timeout - this is normal if location services are slow or unavailable");
                            break;
                        case err.PERMISSION_DENIED:
                            errorMessage = "Location permission denied. Please enable location access in your browser settings.";
                            console.warn("Geolocation permission denied");
                            break;
                        case err.POSITION_UNAVAILABLE:
                            errorMessage = "Location information unavailable. Please check your device's location settings.";
                            console.warn("Geolocation position unavailable");
                            break;
                        default:
                            errorMessage = err.message || "Could not get your location";
                            console.warn("Geolocation error:", err.message);
                    }
                    
                    // Show user-friendly message if notification service is available
                    if (self.notificationService) {
                        self.notificationService.add(_t(errorMessage), { 
                            type: "warning",
                            sticky: false 
                        });
                    }
                    
                    // Set coordinates to null but don't break the flow
                    self.latitude = null;
                    self.longitude = null;
                    self.$('.p_o_glocation_kisok_container').css('display', '');
                    self.def_geolocation.resolve();
                    
                    // Resolve with null instead of rejecting to prevent uncaught promise errors
                    resolve(null);
                },
                {
                    enableHighAccuracy: false,
                    timeout: 15000, // Increased to 15 seconds for better reliability
                    maximumAge: 300000 // Allow cached positions up to 5 minutes old (more lenient)
                }
            );
        });
        
        // Add catch handler to prevent uncaught promise errors
        self.geolocationPromise = self.geolocationPromise.catch(err => {
            console.warn("Geolocation promise error caught:", err);
            return null; // Return null instead of throwing
        });
        
        return self.geolocationPromise;
    },
    
    _getLocationName: async function(latitude, longitude) {
        const self = this;
        
        try {
            // Use Nominatim (OpenStreetMap) reverse geocoding API (free, no API key required)
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`,
                {
                    headers: {
                        'User-Agent': 'Odoo-Attendance-Portal/1.0' // Required by Nominatim
                    }
                }
            );
            
            if (response.ok) {
                const data = await response.json();
                if (data && data.address) {
                    // Build a readable address from the response
                    const addressParts = [];
                    
                    // Try to get a meaningful address
                    if (data.address.road) addressParts.push(data.address.road);
                    if (data.address.suburb || data.address.neighbourhood) {
                        addressParts.push(data.address.suburb || data.address.neighbourhood);
                    }
                    if (data.address.city || data.address.town || data.address.village) {
                        addressParts.push(data.address.city || data.address.town || data.address.village);
                    }
                    if (data.address.state) addressParts.push(data.address.state);
                    if (data.address.country) addressParts.push(data.address.country);
                    
                    self.locationName = addressParts.length > 0 
                        ? addressParts.join(', ') 
                        : (data.display_name || 'Location');
                    
                    console.log("Location name retrieved:", self.locationName);
                } else {
                    self.locationName = 'Location';
                }
            } else {
                throw new Error("Reverse geocoding failed");
            }
        } catch (error) {
            console.warn("Could not get location name:", error);
            self.locationName = 'Location';
        }
    },
    
    _updateGeolocationDisplay: function() {
        const self = this;
        
        const viewElement = self.$('.p_o_glocation_kisok_view');
        if (!viewElement.length) {
            console.warn("Geolocation view element not found");
            return;
        }
        
        // Format coordinates to 6 decimal places
        const latFormatted = self.latitude ? self.latitude.toFixed(6) : 'N/A';
        const lonFormatted = self.longitude ? self.longitude.toFixed(6) : 'N/A';
        
        // Build display HTML
        let displayHTML = '';
        
        if (self.locationName && self.locationName !== 'Location') {
            displayHTML += `<div style="font-weight: bold; margin-bottom: 8px; color: #333;">${self.locationName}</div>`;
        } else if (!self.latitude || !self.longitude) {
            displayHTML += `<div style="font-style: italic; margin-bottom: 8px; color: #666;">Getting location...</div>`;
        }
        
        displayHTML += `<div style="font-size: 0.9em; color: #555;">`;
        displayHTML += `<span><strong>Latitude:</strong> ${latFormatted}</span><br/>`;
        displayHTML += `<span><strong>Longitude:</strong> ${lonFormatted}</span>`;
        displayHTML += `</div>`;
        
        // Update the element - the template has a span inside a div, so update the span or the div
        const element = viewElement[0];
        if (element) {
            // Check if there's a span inside
            const innerSpan = element.querySelector('span');
            if (innerSpan) {
                innerSpan.innerHTML = displayHTML;
            } else {
                // If no span, update the div directly
                element.innerHTML = displayHTML;
            }
            console.log("Geolocation display updated:", {
                latitude: latFormatted,
                longitude: lonFormatted,
                locationName: self.locationName
            });
        }
    },
    
    update_attendance: async function () {
        const self = this;

        // Prevent multiple simultaneous executions
        if (self.isProcessingAttendance) {
            console.log("Attendance already being processed, ignoring request");
            return;
        }

        // Set processing state
        self.isProcessingAttendance = true;
        console.log("Starting attendance processing...");
        
        // Show validation status
        self.notificationService.add(
            _t("Validating location and checking requirements..."),
            { type: "info" }
        );

        // Disable button immediately to prevent further clicks and show processing
        self._disableButton(true);

        // Reset data variables
        self.data_latitude = null;
        self.data_longitude = null;
        self.data_is_inside = false;
        self.data_geofence_ids = [];          
        self.data_photo = null;
        self.data_ip_address = self.ip || null;

        try {
            // Create an array of promises to run in parallel
            const promises = [];
            
            // Add geofence validation if enabled
            if (self.hr_attendance_geofence_p) {
                console.log("Geofence validation is enabled, running validation...");
                self.notificationService.add(
                    _t("Checking geofence location..."),
                    { type: "info" }
                );
                if (window.location.protocol !== 'https:') {
                    console.warn("Geofence validation requires HTTPS");
                    self.notificationService.add(
                        _t("Geofence validation requires HTTPS connection."),
                        { type: "warning" }
                    );
                    // Don't block attendance if not HTTPS, but warn user
                    promises.push(Promise.resolve({ success: true, skipped: true, message: "HTTPS required" }));
                } else {
                    const geofencePromise = self._validate_Geofence()
                        .then(result => {
                            console.log("Geofence validation successful:", result);
                            if (result.geofence_ids && result.geofence_ids.length > 0) {
                                self.notificationService.add(
                                    _t("Location verified: You are in an allowed geofence zone."),
                                    { type: "success" }
                                );
                            } else if (result.no_restriction) {
                                self.notificationService.add(
                                    _t("No geofence restrictions for your location."),
                                    { type: "info" }
                                );
                            }
                            return result;
                        })
                        .catch(error => {
                            console.error("Geofence validation failed:", error);
                            self.notificationService.add(
                                _t("Geofence validation failed: " + error.message),
                                { type: "danger" }
                            );
                            // Return error to block attendance
                            return { success: false, error: error.message };
                        });
                    promises.push(geofencePromise);
                }
            } else {
                console.log("Geofence validation is disabled");
            }
            
            // Add geolocation validation if enabled
            if (self.hr_attendance_geolocation_p && window.location.protocol === 'https:') {
                const geolocationPromise = self._validate_Geolocation().catch(error => {
                    console.error("Geolocation validation failed:", error);
                    // Continue with attendance even if geolocation fails
                    return { success: false, error: error.message };
                });
                promises.push(geolocationPromise);
            }
            
            // Add photo validation if enabled
            if (self.hr_attendance_face_recognition_p) {
                // Check if we're on HTTPS (required for camera access)
                if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
                    self.notificationService.add(
                        _t("Face recognition requires HTTPS connection. Please use a secure connection."),
                        { type: "warning" }
                    );
                    return; // Block check-in if HTTPS is required but not available
                }
                
                // If employee has face descriptors, face recognition is REQUIRED
                if (self.employee_has_face_descriptors) {
                    self.faceRecognitionPromise = new Promise((resolve, reject) => {
                        self.photoPromiseResolve = resolve;
                        self.photoPromiseReject = reject;
                        self._validate_face_recognition();
                    }).then(result => {
                        // Only allow if face recognition succeeded
                        if (result && result.success && !result.skipped) {
                            return { success: true, photo: self.data_photo };
                        } else if (result && result.skipped) {
                            // This shouldn't happen if employee has descriptors, but handle it
                            return { success: false, error: "Face recognition is required but was skipped" };
                        } else {
                            return { success: false, error: "Face recognition failed" };
                        }
                    }).catch(error => {
                        console.error("Photo validation failed:", error);
                        return { success: false, error: error.message || "Face recognition validation failed" };
                    });
                    promises.push(self.faceRecognitionPromise);
                } else {
                    // Employee doesn't have descriptors, allow check-in without face recognition
                    console.log("Employee has no face descriptors - allowing check-in without face recognition");
                }
            }

            // Add device checking if enabled
            const deviceCheckPromise = self._check_device_access().catch(error => {
                console.error("Device check failed:", error);
                return { success: false, error: error.message };
            });
            promises.push(deviceCheckPromise);

            console.log("Starting validation processes...");
            
            // Wait for all validations to complete (or fail)
            const results = await Promise.allSettled(promises);
            
            console.log("All validation processes completed:", results);

            // Extract fulfilled values and check for undefined
            const fulfilledResults = results
                .filter(result => result.status === "fulfilled")
                .map(result => result.value);

            // Check for face recognition requirement - it's mandatory if enabled and employee has descriptors
            if (self.hr_attendance_face_recognition_p && self.employee_has_face_descriptors && self.faceRecognitionPromise) {
                const faceRecognitionIndex = promises.indexOf(self.faceRecognitionPromise);
                if (faceRecognitionIndex >= 0 && faceRecognitionIndex < results.length) {
                    const faceRecognitionResult = results[faceRecognitionIndex];
                    
                    if (faceRecognitionResult.status === 'rejected') {
                        const errorMsg = faceRecognitionResult.reason?.message || "Face recognition validation failed";
                        console.error("Face recognition validation failed (rejected):", errorMsg);
                        self.notificationService.add(
                            _t("Face recognition is required. Please complete the face scan to check in."),
                            { type: "danger", title: _t("Face Recognition Required") }
                        );
                        // Re-enable button so user can try again
                        self.isProcessingAttendance = false;
                        setTimeout(() => {
                            self._enableButton();
                        }, 100);
                        return; // Block check-in
                    }
                    
                    if (faceRecognitionResult.status === 'fulfilled') {
                        const faceResult = faceRecognitionResult.value;
                        if (!faceResult || !faceResult.success || faceResult.skipped) {
                            const errorMsg = faceResult?.error || "Face recognition validation failed";
                            console.error("Face recognition validation failed (fulfilled but invalid):", errorMsg);
                            self.notificationService.add(
                                _t("Face recognition is required. Please complete the face scan to check in."),
                                { type: "danger", title: _t("Face Recognition Required") }
                            );
                            // Re-enable button so user can try again
                            self.isProcessingAttendance = false;
                            setTimeout(() => {
                                self._enableButton();
                            }, 100);
                            return; // Block check-in
                        }
                        console.log("Face recognition validation passed:", faceResult);
                    }
                } else {
                    // Face recognition promise was not found in results - this shouldn't happen
                    console.error("Face recognition promise not found in results");
                    self.notificationService.add(
                        _t("Face recognition validation error. Please try again."),
                        { type: "danger", title: _t("Face Recognition Error") }
                    );
                    // Re-enable button so user can try again
                    self.isProcessingAttendance = false;
                    setTimeout(() => {
                        self._enableButton();
                    }, 100);
                    return; // Block check-in
                }
            }
            
            const hasInvalidResults = fulfilledResults.some(value => 
                value === undefined || 
                (value && value.error && !value.skipped)
            );

            if (hasInvalidResults) {
                const errorMessages = fulfilledResults
                    .filter(value => value && value.error && !value.skipped)
                    .map(value => value.error)
                    .join(", ");
            
                console.error("Cannot proceed due to validation errors:", errorMessages || "Undefined values detected");
                self.notificationService.add(
                    _t("Validation failed: " + (errorMessages || "Unknown error")),
                    { type: "warning" }
                );
                // Re-enable button so user can try again
                self.isProcessingAttendance = false;
                setTimeout(() => {
                    self._enableButton();
                }, 100);
                return;
            }

            // Proceed only if we have valid data
            // Get reason if enabled
            let reason = null;
            if (self.hr_attendance_reason_p) {
                const inputReason = self.$('.p_o_attendance_reasons')[0];
                if (inputReason && inputReason.value) {
                    reason = inputReason.value;
                }
            }

            await self._manual_attendance(
                self.data_latitude, 
                self.data_longitude, 
                self.data_geofence_ids, 
                self.data_ip_address, 
                self.data_photo,
                reason
            );
            
            // Update UI after successful attendance
            await self.update_attendance_kiosk_gui();
            
        } catch (error) {
            console.error("Error during attendance update:", error);
            self.notificationService.add(
                _t("Failed to update attendance. Please try again."),
                { type: "danger" }
            );
        } finally {
            // Always reset processing state and re-enable button
            // But only if we're not already in the process of re-enabling (from dialog close)
            if (!self.isProcessingAttendance) {
                // Button was already re-enabled (e.g., from dialog close), just check cooldown
                setTimeout(() => {
                    self._checkCooldown(); // This will enable/disable based on cooldown
                }, 1000);
            } else {
                // Normal completion, reset and re-enable
                self.isProcessingAttendance = false;
                console.log("Attendance processing completed, re-enabling button");
                setTimeout(() => {
                    self._checkCooldown(); // This will enable/disable based on cooldown
                }, 1000);
            }
        }
    },
    
    _validate_Geolocation: async function() {
        const self = this;
        
        try {
            // Use existing geolocation data if available
            if (self.latitude && self.longitude) {
                self.data_latitude = self.latitude;
                self.data_longitude = self.longitude;
                return { success: true, latitude: self.latitude, longitude: self.longitude };
            }
            
            // Otherwise, get new geolocation data
            let geoResult = null;
            if (!self.geolocationPromise) {
                geoResult = await self._getGeolocation();
            } 
            else {
                geoResult = await self.geolocationPromise;
            }
            
            // Check if we got valid geolocation data
            if (geoResult && geoResult.latitude && geoResult.longitude) {
                self.latitude = geoResult.latitude;
                self.longitude = geoResult.longitude;
                self.data_latitude = self.latitude;
                self.data_longitude = self.longitude;
                return { success: true, latitude: self.latitude, longitude: self.longitude };
            }
            
            // If geolocation is not available, return a failure object instead of throwing
            // This allows the attendance to proceed without geolocation
            console.warn("Geolocation not available - attendance will proceed without location data");
            return { 
                success: false, 
                error: "Geolocation not available. Attendance will be recorded without location data." 
            };
        } 
        catch (error) {
            console.warn("Geolocation validation error (non-blocking):", error);
            // Return failure object instead of rejecting to prevent uncaught promise errors
            return { 
                success: false, 
                error: error.message || "Geolocation validation failed" 
            };
        }
    },

    _validate_Geofence: async function() {
        const self = this;
        console.log("=== Starting Geofence Validation ===");
        self.geofence_data = [];
        
        // Initialize return values
        self.data_is_inside = false;
        self.data_geofence_ids = [];
    
        if (window.location.protocol !== 'https:') {
            console.warn("Geofence validation requires HTTPS");
            return Promise.reject(new Error("HTTPS required for geofence validation"));
        }
    
        try {
            console.log("Employee data:", self.employee);
            if (!self.employee || !self.employee.id || !self.employee.company_id) {
                console.error("Employee data not available:", {
                    employee: self.employee,
                    hasId: self.employee?.id,
                    hasCompanyId: self.employee?.company_id
                });
                throw new Error("Employee data not available");
            }
            
            console.log("Employee ID:", self.employee.id, "Company ID:", self.employee.company_id);
    
            // Get current position if not already available
            let coords;
            if (self.latitude && self.longitude) {
                coords = ol.proj.fromLonLat([self.longitude, self.latitude]);
            } 
            else {
                try {
                    const geolocation = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(
                            ({ coords: { latitude, longitude } }) => {
                                self.latitude = latitude;
                                self.longitude = longitude;
                                resolve({ latitude, longitude });
                            },
                            (err) => {
                                // Handle timeout and other errors gracefully
                                if (err.code === err.TIMEOUT) {
                                    console.warn("Geolocation timeout for geofence validation:", err.message);
                                } else {
                                    console.warn("Geolocation error for geofence validation:", err.message);
                                }
                                reject(err);
                            },
                            { 
                                enableHighAccuracy: false,
                                timeout: 15000, // Increased to 15 seconds
                                maximumAge: 300000 // Allow cached positions up to 5 minutes old
                            }
                        );
                    });
                    coords = ol.proj.fromLonLat([geolocation.longitude, geolocation.latitude]);
                } 
                catch (geoError) {
                    // Don't throw error - allow geofence validation to continue without exact location
                    console.warn("Could not get location for geofence validation (non-blocking):", geoError.message);
                    if (self.notificationService) {
                        self.notificationService.add(
                            _t("Could not get your location. Geofence validation will use approximate location."), 
                            { type: "warning", sticky: false }
                        );
                    }
                    // Use default coordinates (center of map) instead of throwing error
                    coords = ol.proj.fromLonLat([0, 0]);
                }
            }
            
            // Get geofence data from cache or server
            if (!self._geofenceCache) {
                self._geofenceCache = {};
            }
            
            const cacheKey = `${self.employee.id}_${self.employee.company_id[0]}`;
            let geofenceData;
            
            if (self._geofenceCache[cacheKey] && 
                (Date.now() - self._geofenceCache[cacheKey].timestamp < 5 * 60 * 1000)) {
                geofenceData = self._geofenceCache[cacheKey].data;
                self.geofence_data = geofenceData;
            } 
            else {
                geofenceData = await rpc("/hr_attendance/get_geofence_data", { 
                    company_id: self.employee.company_id[0], 
                    employee_id: self.employee.id 
                });
    
                self.geofence_data = Array.isArray(geofenceData) ? geofenceData : [];
    
                // Cache the data
                self._geofenceCache[cacheKey] = {
                    data: self.geofence_data,
                    timestamp: Date.now()
                };
            }
            
            // If no geofence zones are assigned to employee, allow attendance without restriction
            if (!self.geofence_data.length) {
                console.log("No geofence zones assigned to employee - allowing attendance without geofence restriction");
                return { success: true, geofence_ids: [], no_restriction: true };
            }
            
            console.log("Found", self.geofence_data.length, "geofence zones for employee");
            
            // Check if OpenLayers is available
            if (typeof ol === 'undefined') {
                console.error("OpenLayers not loaded");
                throw new Error("OpenLayers not loaded");
            }
        
            console.log("Checking if user is inside geofence zones. Current location:", {
                latitude: self.latitude,
                longitude: self.longitude,
                coords: coords
            });
        
            // Check if user is inside any geofence
            const batchSize = 5;
            for (let i = 0; i < self.geofence_data.length; i += batchSize) {
                const batch = self.geofence_data.slice(i, i + batchSize);
                
                const results = await Promise.all(batch.map(async (record) => {
                    try {
                        const value = JSON.parse(record.overlay_paths);
                        if (Object.keys(value).length === 0) {
                            return null;
                        }
                        
                        const features = new ol.format.GeoJSON().readFeatures(value);
                        if (!features || features.length === 0) {
                            return null;
                        }
                        
                        const geometry = features[0].getGeometry();
                        const isInside = geometry.intersectsCoordinate(coords);
                        console.log(`Geofence ${record.id}: isInside=${isInside}`);
                        if (isInside) {
                            return parseInt(record.id);
                        }
                    } 
                    catch (parseError) {
                        console.error("Error processing geofence record:", parseError);
                    }
                    return null;
                }));
                
                const validIds = results.filter(id => id !== null);
                if (validIds.length > 0) {
                    self.data_is_inside = true;
                    self.data_geofence_ids = validIds;
                    console.log("User is inside geofence zones:", validIds);
                    break;
                }
            }
            
            if (self.data_is_inside) {
                console.log("=== Geofence Validation SUCCESS ===");
                return { success: true, geofence_ids: self.data_geofence_ids };
            } 
            else {
                console.log("=== Geofence Validation FAILED - User not in any zone ===");
                if (self.notificationService) {
                    self.notificationService.add(
                        _t("You haven't entered any of the geofence zones. Please move to an allowed location and try again."),
                        { type: "danger" }
                    );
                }
                // Reject the promise instead of returning a success: false object
                throw new Error("Not in any geofence zone");
            }
        } 
        catch (error) {
            console.error("Geofence validation error:", error);
            if (self.notificationService) {
                self.notificationService.add(
                    _t("Failed to validate geofence: " + error.message),
                    { type: "danger" }
                );
            }
            // Reject the promise with the error
            return Promise.reject(error);
        }
    },
    
    _manual_attendance: async function (latitude, longitude, geofence_ids, ip_address, img64, reason) {
        const self = this;
        try {
            console.log("Recording attendance with data:", {
                latitude, 
                longitude, 
                geofence_ids, 
                ip_address, 
                reason,
                "image": img64 ? "provided" : "not provided"
            });

            const result = await rpc('/hr_attendance/portal_manual_selection', {
                'employee_id': parseInt(this.employee_id),
            });
            
            if (!result || !result.attendance || !result.attendance.id) {
                throw new Error("Failed to create attendance record");
            }

            if (result.attendance_state === "checked_in") {
                await rpc('/hr_attendance/update_portal_checkin_data', {
                    'attendance_id': parseInt(result.attendance.id),
                    'image': img64,
                    'check_in_latitude': latitude,
                    'check_in_longitude': longitude,
                    'check_in_geofence_ids': geofence_ids,
                    'check_in_ipaddress': ip_address,
                    'check_in_reason': reason || false,
                });
                
                self.notificationService.add(
                    _t("Check-in recorded successfully."),
                    { type: "success" }
                );
            } 
            else if (result.attendance_state === "checked_out") {
                await rpc('/hr_attendance/update_portal_checkout_data', {
                    'attendance_id': parseInt(result.attendance.id),
                    'image': img64,
                    'check_out_latitude': latitude,
                    'check_out_longitude': longitude,
                    'check_out_geofence_ids': geofence_ids,
                    'check_out_ipaddress': ip_address,
                    'check_out_reason': reason || false,
                });
                
                self.notificationService.add(
                    _t("Check-out recorded successfully."),
                    { type: "success" }
                );
            }

            // Clear Data
            self.data_latitude = null;
            self.data_longitude = null;
            self.data_photo = null;
            self.data_geofence_ids = [];
            self.data_ip_address = null;
            
            // Note: Cooldown check is handled in the finally block of update_attendance
            return true;
        } 
        catch (error) {
            console.error("Error in manual attendance:", error);
            self.notificationService.add(
                _t("Failed to record attendance. Please try again."),
                { type: "danger" }
            );
            throw error;
        }
    },
    
    _validate_face_recognition: async function() {
        const self = this;
    
        // If employee doesn't have face descriptors, allow check-in without face recognition
        // This should not happen if called from update_attendance when descriptors exist, but handle it
        if (!self.employee_has_face_descriptors) {
            console.log("Employee has no face descriptors - allowing check-in without face recognition");
            if (self.photoPromiseResolve) {
                self.photoPromiseResolve({ success: true, photo: null, skipped: true });
            }
            return;
        }
    
        // Ensure face-api.js is loaded
        try {
            await self._loadFaceapi();
            
            if (typeof faceapi === 'undefined') {
                throw new Error("Face API not loaded");
            }
        } catch (error) {
            console.error("Failed to load Face API:", error);
            const errorMsg = "Failed to load face recognition library. Please refresh the page and try again.";
            if (self.photoPromiseReject) {
                self.photoPromiseReject(new Error(errorMsg));
            }
            if (self.notificationService) {
                self.notificationService.add(
                    _t(errorMsg),
                    { type: "danger", title: _t("Face Recognition Error") }
                );
            }
            return;
        }
        
        // Load face descriptors if not already loaded
        if (!self.labeledFaceDescriptors || !self.labeledFaceDescriptors.length) {
            console.log("Face descriptors not loaded, loading now...");
            try {
                // Initialize load_label if it doesn't exist
                if (!self.load_label) {
                    self.load_label = new Deferred();
                }
                
                // Check if models are already loaded by trying to use faceapi
                let modelsLoaded = false;
                try {
                    if (typeof faceapi !== 'undefined' && 
                        faceapi.nets && 
                        faceapi.nets.tinyFaceDetector && 
                        faceapi.nets.tinyFaceDetector.params) {
                        modelsLoaded = true;
                    }
                } catch (e) {
                    // Models not loaded
                }
                
                // Ensure models are loaded first
                if (!modelsLoaded) {
                    console.log("Loading face recognition models...");
                    await self.load_models();
                } else {
                    // Models are loaded, just load the labeled images
                    console.log("Models already loaded, loading labeled images...");
                    await self.loadLabeledImages();
                }
                
                // Check again after loading
                if (!self.labeledFaceDescriptors || !self.labeledFaceDescriptors.length) {
                    const errorMsg = "No face descriptors found. Please add face images to your profile.";
                    console.error(errorMsg);
                    if (self.photoPromiseReject) {
                        self.photoPromiseReject(new Error(errorMsg));
                    }
                    if (self.notificationService) {
                        self.notificationService.add(
                            _t(errorMsg),
                            { type: "danger", title: _t("Face Recognition Error") }
                        );
                    }
                    return;
                }
                
                console.log("Face descriptors loaded successfully:", self.labeledFaceDescriptors.length);
            } catch (error) {
                console.error("Failed to load face descriptors:", error);
                const errorMsg = error.message || "Failed to load face recognition data. Please try again.";
                if (self.photoPromiseReject) {
                    self.photoPromiseReject(new Error(errorMsg));
                }
                if (self.notificationService) {
                    self.notificationService.add(
                        _t(errorMsg),
                        { type: "danger", title: _t("Face Recognition Error") }
                    );
                }
                return;
            }
        }
        
        if (!self.dialog) {
            const errorMsg = "Dialog service not available";
            console.error(errorMsg);
            if (self.photoPromiseReject) {
                self.photoPromiseReject(new Error(errorMsg));
            }
            return;
        }
        
        // At this point, faceapi should be loaded and labeledFaceDescriptors should be available
        if (typeof faceapi === 'undefined') {
            const errorMsg = "Face API not loaded";
            console.error(errorMsg);
            if (self.photoPromiseReject) {
                self.photoPromiseReject(new Error(errorMsg));
            }
            return;
        }
        
        // Open the dialog
        try {
            console.log("Opening face recognition dialog - face recognition is REQUIRED");
            console.log("Available face descriptors:", self.labeledFaceDescriptors.length);
            const dialogRef = self.dialog.add(AttendanceRecognitionDialog, {
                faceapi: faceapi,
                labeledFaceDescriptors: self.labeledFaceDescriptors,
                updateRecognitionAttendance: (rdata) => {
                    if (!rdata) {
                        const errorMsg = "No recognition data received";
                        if (self.photoPromiseReject) {
                            self.photoPromiseReject(new Error(errorMsg));
                        }
                        if (self.notificationService) {
                            self.notificationService.add(
                                _t("Face recognition failed. Please try again."),
                                { type: "danger", title: _t("Face Recognition Failed") }
                            );
                        }
                        return;
                    }
                    
                    if (parseInt(self.employee_id) !== parseInt(rdata.employee_id)) {
                        const errorMsg = "The detected employee does not match the logged-in employee";
                        if (self.photoPromiseReject) {
                            self.photoPromiseReject(new Error(errorMsg));
                        }
                        
                        if (self.notificationService) {
                            self.notificationService.add(
                                _t("Face recognition failed: The detected employee does not match your account. Please try again."),
                                { type: "danger", title: _t("Employee Mismatch") }
                            );
                        }
                        return;
                    }
                    
                    if (rdata.image) {
                        self.data_photo = rdata.image;
                        if (self.photoPromiseResolve) {
                            self.photoPromiseResolve({ success: true, photo: rdata.image, skipped: false });
                        }
                    } else {
                        const errorMsg = "No image captured during face recognition";
                        // Re-enable button on error so user can try again
                        self.isProcessingAttendance = false;
                        setTimeout(() => {
                            self._enableButton();
                        }, 100);
                        if (self.photoPromiseReject) {
                            self.photoPromiseReject(new Error(errorMsg));
                        }
                        if (self.notificationService) {
                            self.notificationService.add(
                                _t("Face recognition failed: No image was captured. Please try again."),
                                { type: "danger", title: _t("Face Recognition Failed") }
                            );
                        }
                    }
                },
                close: () => {
                    // Handle dialog close without selection - this should block check-in
                    const errorMsg = "Face recognition was cancelled or closed without detection";
                    console.log("Face recognition dialog close callback triggered, re-enabling button");
                    
                    // Immediately reset processing state
                    self.isProcessingAttendance = false;
                    console.log("isProcessingAttendance set to false");
                    
                    // Re-enable button immediately (no delay)
                    self._enableButton();
                    
                    // Force re-enable multiple times to ensure it works
                    setTimeout(() => {
                        console.log("Backup re-enablement 1");
                        self.isProcessingAttendance = false;
                        self._enableButton();
                    }, 100);
                    
                    setTimeout(() => {
                        console.log("Backup re-enablement 2");
                        self.isProcessingAttendance = false;
                        self._enableButton();
                    }, 300);
                    
                    setTimeout(() => {
                        console.log("Backup re-enablement 3");
                        self.isProcessingAttendance = false;
                        self._enableButton();
                    }, 500);
                    
                    // Reject the promise to block check-in
                    if (self.photoPromiseReject) {
                        self.photoPromiseReject(new Error(errorMsg));
                    }
                    if (self.notificationService) {
                        self.notificationService.add(
                            _t("Face recognition is required. Please complete the face scan to check in."),
                            { type: "warning", title: _t("Face Recognition Required") }
                        );
                    }
                }
            });
            
            // Watch for dialog removal from DOM as a fallback to ensure button is re-enabled
            const dialogCheckInterval = setInterval(() => {
                // Check if dialog still exists in DOM by looking for video element
                const videoElement = document.querySelector('video[id="video"]');
                if (!videoElement && self.isProcessingAttendance) {
                    console.log("Face recognition dialog removed from DOM, re-enabling button as fallback");
                    clearInterval(dialogCheckInterval);
                    self.isProcessingAttendance = false;
                    self._enableButton();
                    // Reject promise if not already rejected
                    if (self.photoPromiseReject) {
                        self.photoPromiseReject(new Error("Face recognition dialog was closed"));
                    }
                }
            }, 300);
            
            // Clear interval after 60 seconds to avoid memory leak
            setTimeout(() => {
                clearInterval(dialogCheckInterval);
            }, 60000);
        } catch (error) {
            console.error("Error opening face recognition dialog:", error);
            // Re-enable button on error so user can try again
            self.isProcessingAttendance = false;
            setTimeout(() => {
                self._enableButton();
            }, 100);
            if (self.photoPromiseReject) {
                self.photoPromiseReject(error);
            }
            if (self.notificationService) {
                self.notificationService.add(
                    _t("Failed to start face recognition. Please try again."),
                    { type: "danger", title: _t("Face Recognition Error") }
                );
            }
        }
    },
    
    update_attendance_kiosk_gui: async function () {
        const self = this;
        
        try {
            const res = await rpc('/pt_attendance_portal/search_read/get_employee_data', {
                'employee_id': parseInt(this.employee_id),
            });
            
            if (res && res.length) {
                self.employee = res[0];
                self._updateAttendanceUI();
                
                // Redirect after a short delay
                window.setTimeout(function() {
                    window.location = '/my/hr_attendances';
                }, 500);
                
                return true;
            }
            
            return false;
        } 
        catch (error) {
            console.error("Failed to update attendance UI:", error);
            return false;
        }
    },
    
    convertNumToTime: function (number) {
        const sign = (number >= 0) ? 1 : -1;
        number = number * sign;
        
        const hour = Math.floor(number);
        let decpart = number - hour;
        
        const min = 1 / 60;
        decpart = min * Math.round(decpart / min);
        
        let minute = Math.floor(decpart * 60) + '';
        if (minute.length < 2) {
            minute = '0' + minute;
        }
        
        const timeSign = sign == 1 ? '' : '-';
        return timeSign + hour + ':' + minute;
    },
    
    _autoExpandGeolocation: function() {
        const self = this;
        
        // Auto-expand if we have coordinates
        if (self.latitude && self.longitude) {
            const toggle = self.$(".p_o_glocation_kisok_toggle");
            const view = self.$('.p_o_glocation_kisok_view');
            
            if (toggle.hasClass('fa-angle-double-down') && view.length) {
                view.css('display', 'block');
                toggle.toggleClass("fa-angle-double-down fa-angle-double-up");
                console.log("Auto-expanded Geo Location tab");
            }
        }
    },
    
    _autoExpandMap: function() {
        const self = this;
        
        // Auto-expand if map is initialized and has features (geofence zones or user location)
        if (self.olmap && self.vectorSource) {
            const features = self.vectorSource.getFeatures();
            if (features.length > 0) {
                const toggle = self.$(".p_o_gmap_kisok_toggle");
                const view = self.$('.p_o_gmap_kisok_view');
                
                if (toggle.hasClass('fa-angle-double-down') && view.length) {
                    view.css('display', 'block');
                    toggle.toggleClass("fa-angle-double-down fa-angle-double-up");
                    console.log("Auto-expanded Google Map Location tab");
                }
            }
        }
    },
    
    _toggle_glocation: function () {
        const self = this;
        
        if (self.$(".p_o_glocation_kisok_toggle").hasClass('fa-angle-double-down')) {
            self.$('.p_o_glocation_kisok_view').css('display', 'block');
            self.$("i.p_o_glocation_kisok_toggle").toggleClass("fa-angle-double-down fa-angle-double-up");
            
            // Always update display when expanded (will show "N/A" if not available yet)
            self._updateGeolocationDisplay();
            
            // If coordinates are not available yet, try to get them
            if (!self.latitude || !self.longitude) {
                console.log("Coordinates not available, attempting to get geolocation...");
                if (navigator.geolocation) {
                    self._getGeolocation().catch(err => {
                        console.warn("Could not get geolocation:", err);
                        self._updateGeolocationDisplay(); // Update to show error state
                    });
                } else {
                    self.locationName = 'Geolocation not supported';
                    self._updateGeolocationDisplay();
                }
            }
        } else {
            self.$('.p_o_glocation_kisok_view').css('display', 'none');
            self.$("i.p_o_glocation_kisok_toggle").toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },

    _initMap: async function () {
        const self = this;
        
        // Check if OpenLayers is available
        if (typeof ol === 'undefined') {
            console.error("OpenLayers not loaded");
            self.$('.p_o_gmap_kisok_container').addClass('d-none');
            self.def_geofence.resolve();
            return true;
        }
        
        const isHTTPS = window.location.protocol === 'https:';
        const hasGeolocation = navigator.geolocation;
        
        try {
            let latitude = null;
            let longitude = null;
            
            // Only get geolocation if HTTPS and available
            if (isHTTPS && hasGeolocation) {
                try {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            enableHighAccuracy: false,
                            maximumAge: 300000, // Allow cached positions up to 5 minutes old
                            timeout: 15000 // Increased to 15 seconds for better reliability
                        });
                    });
                    
                    latitude = position.coords.latitude;
                    longitude = position.coords.longitude;
                    self.latitude = latitude;
                    self.longitude = longitude;
                    console.log("Current location obtained:", latitude, longitude);
                } catch (geoError) {
                    // Handle timeout and other errors gracefully
                    if (geoError.code === geoError.TIMEOUT) {
                        console.warn("Geolocation timeout (will still show geofence zones):", geoError.message);
                    } else {
                        console.warn("Could not get geolocation (will still show geofence zones):", geoError.message);
                    }
                    // Continue without geolocation - we can still show geofence zones
                }
            } else {
                if (!isHTTPS) {
                    console.warn("Not on HTTPS - geolocation disabled, but will show geofence zones");
                }
                if (!hasGeolocation) {
                    console.warn("Geolocation not supported - will show geofence zones only");
                }
            }
            
            if (!self.olmap) {
                const gmap_div = self.$('.p_o_gmap_kisok_view').get(0);
                if (!gmap_div) {
                    console.error("Map container not found");
                    self.def_geofence.resolve();
                    return;
                }
                
                gmap_div.style.width = '550px';
                gmap_div.style.height = '200px';
                
                // Create vector source for features (user location, geofences, etc.)
                const vectorSource = new ol.source.Vector({});
                
                // Create the map with OpenLayers
                self.olmap = new ol.Map({
                    target: gmap_div,
                    layers: [
                        new ol.layer.Tile({
                            source: new ol.source.OSM()
                        }),
                        new ol.layer.Vector({
                            source: vectorSource
                        })
                    ],
                    view: new ol.View({
                        center: ol.proj.fromLonLat([self.longitude, self.latitude]),
                        zoom: 14
                    }),
                    controls: ol.control.defaults({
                        zoom: true,
                        rotate: false,
                        attribution: true
                    }).extend([
                        new ol.control.FullScreen(),
                        new ol.control.ScaleLine()
                    ])
                });
                
                // Store vector source for later use
                self.vectorSource = vectorSource;
                
                // Add a marker for the current position only if we have coordinates
                if (latitude !== null && longitude !== null) {
                    const iconFeature = new ol.Feature({
                        geometry: new ol.geom.Point(ol.proj.fromLonLat([longitude, latitude])),
                        name: 'Current Position'
                    });
                    
                    // Style for the marker
                    const iconStyle = new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: 8,
                            fill: new ol.style.Fill({
                                color: '#3399CC'
                            }),
                            stroke: new ol.style.Stroke({
                                color: '#fff',
                                width: 2
                            })
                        })
                    });
                    
                    iconFeature.setStyle(iconStyle);
                    vectorSource.addFeature(iconFeature);
                }
            }
            
            // Load and display geofence zones (wait for employee data if needed)
            // Try multiple times if employee data isn't ready yet
            let attempts = 0;
            const maxAttempts = 10;
            const attemptLoadGeofences = async () => {
                if (self.employee && self.employee.id && self.employee.company_id) {
                    console.log("Employee data available, loading geofence zones...");
                    await self._loadGeofenceZonesOnMap();
                    
                    // Fit view to show all features (user location + geofences)
                    if (self.vectorSource && self.vectorSource.getFeatures().length > 0) {
                        setTimeout(() => {
                            try {
                                const extent = self.vectorSource.getExtent();
                                if (extent && !isNaN(extent[0]) && !isNaN(extent[1])) {
                                    // Fit the map to show all features (geofences + user location)
                                    // Use minimal padding to fit closely to the actual area
                                    self.olmap.getView().fit(extent, {
                                        padding: [20, 20, 20, 20],  // Minimal padding for close fit
                                        maxZoom: 18
                                        // No minZoom - let it fit based on actual area size
                                    });
                                    
                                    self.olmap.updateSize();
                                    console.log("Map view fitted to show geofence zones, zoom:", self.olmap.getView().getZoom());
                                }
                            } catch (fitError) {
                                console.error("Error fitting map view:", fitError);
                            }
                        }, 300);
                    } else if (self.latitude && self.longitude) {
                        // If no geofences but we have location, zoom to location with reasonable zoom
                        setTimeout(() => {
                            self.olmap.getView().setCenter(ol.proj.fromLonLat([self.longitude, self.latitude]));
                            self.olmap.getView().setZoom(14);  // Reasonable default zoom for single location
                            self.olmap.updateSize();
                        }, 300);
                    }
                } else if (attempts < maxAttempts) {
                    attempts++;
                    console.log(`Employee data not yet available (attempt ${attempts}/${maxAttempts}), retrying...`);
                    setTimeout(attemptLoadGeofences, 500);
                } else {
                    console.warn("Employee data not available after multiple attempts, geofence zones may not load");
                }
            };
            
            // Start attempting to load geofence zones
            attemptLoadGeofences();
            
            // Update map size after rendering
            setTimeout(function() {
                if (self.olmap) {
                    self.olmap.updateSize();
                }
            }, 200);
            
            self.$('.p_o_gmap_kisok_container').css('display', '');
            
            // Auto-expand map if geofence zones are loaded or map is ready
            setTimeout(() => {
                self._autoExpandMap();
            }, 500);
            
            self.def_geofence.resolve();
        } catch (error) {
            console.error("Geolocation error:", error);
            self.$('.p_o_gmap_kisok_container').addClass('d-none');
            self.def_geofence.resolve();
        }
        
        return true;
    },
    
    _loadGeofenceZonesOnMap: async function() {
        const self = this;
        
        if (!self.employee || !self.employee.id || !self.employee.company_id) {
            console.log("Employee data not available for geofence display", {
                hasEmployee: !!self.employee,
                employeeId: self.employee?.id,
                companyId: self.employee?.company_id
            });
            return;
        }
        
        if (!self.olmap || !self.vectorSource) {
            console.log("Map not initialized yet", {
                hasMap: !!self.olmap,
                hasVectorSource: !!self.vectorSource
            });
            return;
        }
        
        try {
            console.log("Loading geofence zones for map display...", {
                employeeId: self.employee.id,
                companyId: self.employee.company_id
            });
            
            const companyId = Array.isArray(self.employee.company_id) ? self.employee.company_id[0] : self.employee.company_id;
            const geofenceData = await rpc("/hr_attendance/get_geofence_data", { 
                company_id: companyId, 
                employee_id: self.employee.id 
            });
            
            console.log("Geofence data received from server:", geofenceData);
            
            const geofences = Array.isArray(geofenceData) ? geofenceData : [];
            console.log("Loaded", geofences.length, "geofence zones for display");
            
            if (geofences.length === 0) {
                console.log("No geofence zones to display for this employee");
                return;
            }
            
            // Add each geofence zone to the map
            geofences.forEach((geofence) => {
                try {
                    if (!geofence.overlay_paths) {
                        return;
                    }
                    
                    let geojson = JSON.parse(geofence.overlay_paths);
                    
                    // Handle both FeatureCollection and Geometry formats
                    let features = [];
                    if (geojson.type === 'FeatureCollection' && geojson.features) {
                        features = new ol.format.GeoJSON().readFeatures(geojson);
                    } else if (geojson.type === 'Feature') {
                        features = [new ol.format.GeoJSON().readFeature(geojson)];
                    } else if (geojson.type === 'Geometry' || geojson.type === 'Polygon') {
                        // Create a Feature from Geometry
                        const feature = new ol.Feature({
                            geometry: new ol.format.GeoJSON().readGeometry(geojson)
                        });
                        features = [feature];
                    } else {
                        // Try to read as features anyway
                        features = new ol.format.GeoJSON().readFeatures(geojson);
                    }
                    
                    console.log(`Processing geofence ${geofence.id} (${geofence.name}):`, geojson.type, features.length, "features");
                    
                    if (features && features.length > 0) {
                        features.forEach((feature) => {
                            // Style for geofence zones - yellow/amber color
                            feature.setStyle(new ol.style.Style({
                                fill: new ol.style.Fill({
                                    color: 'rgba(255, 235, 59, 0.4)' // Yellow with transparency
                                }),
                                stroke: new ol.style.Stroke({
                                    color: '#ffc107', // Yellow/amber border
                                    width: 3
                                })
                            }));
                            
                            // Add name and ID as properties
                            feature.set('name', geofence.name || `Geofence ${geofence.id}`);
                            feature.set('geofence_id', geofence.id);
                            self.vectorSource.addFeature(feature);
                            console.log(`Added geofence zone to map: ${geofence.name} (ID: ${geofence.id})`);
                        });
                    } else {
                        console.warn(`No features extracted from geofence ${geofence.id}`);
                    }
                } catch (parseError) {
                    console.error("Error parsing geofence zone:", geofence.id, parseError);
                }
            });
            
            const addedCount = geofences.filter(g => g.overlay_paths).length;
            console.log(`Successfully added ${addedCount} geofence zone(s) to map`);
            
            // Update map view to show all geofences and user location
            if (self.olmap && self.vectorSource && self.vectorSource.getFeatures().length > 0) {
                setTimeout(() => {
                    try {
                        const extent = self.vectorSource.getExtent();
                        if (extent && !isNaN(extent[0]) && !isNaN(extent[1])) {
                            self.olmap.getView().fit(extent, {
                                padding: [20, 20, 20, 20],  // Minimal padding for close fit
                                maxZoom: 18
                                // No minZoom - let it fit based on actual area size
                            });
                            
                            self.olmap.updateSize();
                            console.log("Map view updated to show geofence zones and user location, zoom:", self.olmap.getView().getZoom());
                        }
                    } catch (fitError) {
                        console.error("Error fitting map view:", fitError);
                    }
                }, 300);
            }
        } catch (error) {
            console.error("Error loading geofence zones for map:", error);
        }
    },

    _getUserIP: async function () {
        const self = this;
        
        try {
            // Use a more reliable service with a timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 7000);
            
            const response = await fetch('https://api.ipify.org?format=json', { 
                signal: controller.signal 
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const data = await response.json();
                if (data.ip) {
                    self.ip = data.ip;
                    self.data_ip_address = data.ip;
                    // Update the display with IP address
                    const ipView = self.$('.p_o_gip_kisok_view span');
                    if (ipView.length) {
                        ipView[0].innerText = "IP: " + data.ip;
                    }
                    self.def_ipaddress.resolve();
                    return data.ip;
                }
            }
            
            throw new Error("Failed to get IP address");
        } 
        catch (error) {
            console.error("IP address error:", error);
            self.ip = 'IP address not available';
            self.data_ip_address = null;
            // Update the display with error message
            const ipView = self.$('.p_o_gip_kisok_view span');
            if (ipView.length) {
                ipView[0].innerText = "IP: Not available";
            }
            self.def_ipaddress.resolve();
            return null;
        }
    },

    _toggle_olmap: function () {
        const self = this;
        
        if (self.$(".p_o_gmap_kisok_toggle").hasClass('fa-angle-double-down')) {
            self.$('.p_o_gmap_kisok_view').css('display', 'block');
            self.$("i.p_o_gmap_kisok_toggle").toggleClass("fa-angle-double-down fa-angle-double-up");
            
            // Update map size after showing and reload geofence zones if needed
            if (self.olmap) {
                setTimeout(async function() {
                    self.olmap.updateSize();
                    
                    if (self.latitude && self.longitude) {
                        self.olmap.getView().setCenter(
                            ol.proj.fromLonLat([self.longitude, self.latitude])
                        );
                    }
                    
                    // If employee data is available but geofence zones aren't loaded yet, load them now
                    if (self.employee && self.employee.id && self.employee.company_id && self.vectorSource) {
                        const hasGeofences = Array.from(self.vectorSource.getFeatures()).some(f => 
                            f.get('geofence_id') !== undefined
                        );
                        
                        if (!hasGeofences) {
                            console.log("Map expanded, loading geofence zones now...");
                            await self._loadGeofenceZonesOnMap();
                            
                            if (self.vectorSource.getFeatures().length > 0) {
                                try {
                                    const extent = self.vectorSource.getExtent();
                                    if (extent && !isNaN(extent[0]) && !isNaN(extent[1])) {
                                        self.olmap.getView().fit(extent, {
                                            padding: [20, 20, 20, 20],  // Minimal padding for close fit
                                            maxZoom: 18
                                            // No minZoom - let it fit based on actual area size
                                        });
                                        
                                        self.olmap.updateSize();
                                        console.log("Map view updated with geofence zones, zoom:", self.olmap.getView().getZoom());
                                    }
                                } catch (fitError) {
                                    console.error("Error fitting map view:", fitError);
                                }
                            }
                        }
                    }
                }, 200);
            }
        } else {
            self.$('.p_o_gmap_kisok_view').css('display', 'none');
            self.$("i.p_o_gmap_kisok_toggle").toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    
    _toggle_gip: function () {
        const self = this;
        
        if (self.$(".p_o_gip_kisok_toggle").hasClass('fa-angle-double-down')) {
            self.$('.p_o_gip_kisok_view').toggle('show');
            self.$("i.p_o_gip_kisok_toggle").toggleClass("fa-angle-double-down fa-angle-double-up");
            
            if (self.ip) {
                self.$('.p_o_gip_kisok_view span')[0].innerText = "IP: " + self.ip;
            }
        } else {
            self.$('.p_o_gip_kisok_view').toggle('hide');
            self.$("i.p_o_gip_kisok_toggle").toggleClass("fa-angle-double-up fa-angle-double-down");
        }
    },
    
    _on_change_reason: function() {
        const self = this;
        const inputReason = this.$('.p_o_attendance_reasons')[0];
        
        if (inputReason && inputReason.value !== '') {
            self.attendance_reason = inputReason.value;
        }
    },

    _get_device_info: function() {
        const self = this;
        console.log("Getting device information...");
        
        // Generate device information similar to Odoo 16 version
        const deviceInfo = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            screenResolution: screen.width + 'x' + screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            pseudoMAC: self._generate_pseudo_mac(),
            deviceName: self._generate_device_name()
        };
        
        return deviceInfo;
    },

    _generate_device_name: function() {
        const userAgent = navigator.userAgent;
        const platform = navigator.platform || '';
        let deviceName = '';
        let deviceType = 'other';
        
        // Device type detection
        if (/Mobile|Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)) {
            deviceName = 'Mobile Device';
            deviceType = 'mobile';
        } else if (/iPad|Tablet/i.test(userAgent) || (platform.indexOf('iPad') !== -1)) {
            deviceName = 'Tablet';
            deviceType = 'tablet';
        } else if (/Windows/i.test(userAgent)) {
            if (/Mobile|Tablet|Touch/i.test(userAgent) || 
                (screen.width <= 1366 && screen.height <= 768) ||
                (screen.width <= 1600 && screen.height <= 900)) {
                deviceName = 'Windows Laptop';
                deviceType = 'laptop';
            } else {
                deviceName = 'Windows Desktop';
                deviceType = 'desktop';
            }
        } else if (/Mac/i.test(userAgent)) {
            if (/Mobile|Tablet|Touch/i.test(userAgent) || 
                (screen.width <= 1440 && screen.height <= 900) ||
                (screen.width <= 1680 && screen.height <= 1050)) {
                deviceName = 'Mac Laptop';
                deviceType = 'laptop';
            } else {
                deviceName = 'Mac Desktop';
                deviceType = 'desktop';
            }
        } else if (/Linux/i.test(userAgent)) {
            deviceName = 'Linux Computer';
            deviceType = 'desktop';
        } else {
            deviceName = 'Unknown Device';
            deviceType = 'other';
        }
        
        // Browser detection
        let browser = '';
        if (userAgent.indexOf('Edg') !== -1) {
            browser = 'Edge';
        } else if (userAgent.indexOf('Chrome') !== -1 && userAgent.indexOf('Edg') === -1) {
            browser = 'Chrome';
        } else if (userAgent.indexOf('Firefox') !== -1) {
            browser = 'Firefox';
        } else if (userAgent.indexOf('Safari') !== -1 && userAgent.indexOf('Chrome') === -1 && userAgent.indexOf('Edg') === -1) {
            browser = 'Safari';
        } else if (userAgent.indexOf('Opera') !== -1 || userAgent.indexOf('OPR') !== -1) {
            browser = 'Opera';
        } else if (userAgent.indexOf('MSIE') !== -1 || userAgent.indexOf('Trident') !== -1) {
            browser = 'Internet Explorer';
        } else {
            browser = 'Unknown Browser';
        }
        
        // Store device type for later use
        window.currentDeviceType = deviceType;
        
        return deviceName + ' (' + browser + ')';
    },

    _generate_pseudo_mac: function() {
        // Generate a pseudo-MAC address based on device characteristics
        const components = [
            navigator.userAgent.length.toString(16).padStart(2, '0'),
            navigator.platform.length.toString(16).padStart(2, '0'),
            screen.width.toString(16).padStart(2, '0'),
            screen.height.toString(16).padStart(2, '0'),
            new Date().getTimezoneOffset().toString(16).padStart(2, '0'),
            navigator.language.length.toString(16).padStart(2, '0')
        ];
        
        return components.join(':').toUpperCase();
    },

    _check_device_access: async function() {
        const self = this;
        console.log("Checking device access for employee:", self.employee_id);
        
        try {
            const deviceInfo = self._get_device_info();
            console.log("Device info:", deviceInfo);
            
            const response = await rpc('/pt_attendance_portal/device/check', {
                employee_id: parseInt(self.employee_id),
                device_mac: deviceInfo.pseudoMAC,
                device_name: deviceInfo.deviceName,
                device_type: window.currentDeviceType || 'other'
            });
            
            console.log("Device check response:", response);
            
            if (response && response.success) {
                if (response.auto_added) {
                    console.log("Device was automatically added:", response.message);
                    self.notificationService.add(
                        _t("Device automatically added: " + response.message),
                        { type: "success" }
                    );
                }
                return { success: true, message: response.message };
            } else {
                const errorMessage = response ? response.message : 'Device not authorized';
                console.error("Device not authorized:", errorMessage);
                
                self.notificationService.add(
                    _t("Device not authorized: " + errorMessage + ". Please contact your administrator to add this device to your allowed devices list."),
                    { type: "danger" }
                );
                
                return { success: false, error: errorMessage };
            }
        } catch (error) {
            console.error("Device check error:", error);
            
            // If device check fails, log the error but don't block attendance
            console.log("Device check failed, proceeding with attendance anyway");
            return { success: true, message: "Device check failed, proceeding anyway" };
        }
    },

    _disableButton: function(showProcessing = false) {
        // Find all possible attendance buttons
        const buttons = document.querySelectorAll('.p_o_hr_attendance_sign_in_out_icon, .hr_attendance_sign_in_icon, .hr_attendance_sign_out_icon');
        console.log("Found buttons:", buttons);
        
        buttons.forEach(button => {
            console.log("Disabling button:", button.className);
            button.style.pointerEvents = 'none';
            button.style.opacity = '0.7';
            button.style.cursor = 'not-allowed';
            button.style.transition = 'all 0.3s ease';
            
            // Add processing indicator if requested
            if (showProcessing) {
                const originalText = button.innerHTML;
                // Create elegant processing indicator
                button.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                        <i class="fa fa-spinner processing-spinner"></i>
                        <span class="processing-text">Processing...</span>
                    </div>
                `;
                button.setAttribute('data-original-text', originalText);
                
                // Add processing class and simple animation
                button.classList.add('attendance-processing');
                button.style.animation = 'pulse 2s ease-in-out infinite';
            }
        });
    },

    _enableButton: function() {
        // Find all possible attendance buttons
        const buttons = document.querySelectorAll('.p_o_hr_attendance_sign_in_out_icon, .hr_attendance_sign_in_icon, .hr_attendance_sign_out_icon');
        console.log("Enabling buttons:", buttons.length, "buttons found");
        
        if (buttons.length === 0) {
            console.warn("No attendance buttons found to enable");
            return;
        }
        
        buttons.forEach(button => {
            console.log("Enabling button:", button.className);
            
            // Remove any animations and processing classes
            button.style.animation = 'none';
            button.classList.remove('attendance-processing');
            
            // Remove processing spinner and text if present
            const spinner = button.querySelector('.processing-spinner');
            const processingText = button.querySelector('.processing-text');
            if (spinner) {
                spinner.remove();
            }
            if (processingText) {
                processingText.remove();
            }
            
            // Restore original text if it was changed
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
                button.removeAttribute('data-original-text');
            }
            
            // Enable button with smooth transition
            button.style.pointerEvents = 'auto';
            button.style.opacity = '1';
            button.style.cursor = 'pointer';
            button.style.transition = 'all 0.3s ease';
            button.disabled = false;
            
            // Remove any disabled attributes
            button.removeAttribute('disabled');
            button.removeAttribute('aria-disabled');
        });
        
        console.log("Buttons enabled, isProcessingAttendance:", this.isProcessingAttendance);
    },

    _checkCooldown: async function() {
        if (!this.employee_id) {
            console.log("No employee_id, enabling button");
            this._enableButton();
            return;
        }
        
        try {
            console.log("Checking cooldown for employee:", this.employee_id);
            const result = await rpc('/pt_attendance_portal/cooldown/check', {
                'employee_id': parseInt(this.employee_id),
            });
            
            console.log("Cooldown check result:", result);
            
            if (result.success) {
                console.log("No cooldown, enabling button");
                this._enableButton();
            } else {
                console.log("Cooldown active, starting countdown");
                // Start countdown
                this._startCountdown(result.message);
            }
        } catch (error) {
            console.error("Cooldown check error:", error);
            this._enableButton(); // Enable on error
        }
    },

    _startCountdown: function(message) {
        const timeMatch = message.match(/(\d+) minutes and (\d+) seconds/);
        if (!timeMatch) return;
        
        let totalSeconds = parseInt(timeMatch[1]) * 60 + parseInt(timeMatch[2]);
        console.log("Starting countdown with", totalSeconds, "seconds remaining");
        
        // Create countdown display
        let countdownElement = document.querySelector('.cooldown-countdown');
        if (!countdownElement) {
            countdownElement = document.createElement('div');
            countdownElement.className = 'cooldown-countdown';
            countdownElement.style.cssText = `
                text-align: center;
                margin-top: 10px;
                padding: 15px;
                background: linear-gradient(135deg, #f8d7da, #f5c6cb);
                color: #721c24;
                border: 2px solid #f5c6cb;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            `;
            
            // Insert after the attendance button
            const button = document.querySelector('.p_o_hr_attendance_sign_in_out_icon');
            if (button && button.parentNode) {
                button.parentNode.insertBefore(countdownElement, button.nextSibling);
            }
        }
        
        const updateCountdown = () => {
            if (totalSeconds <= 0) {
                this._enableButton();
                // Remove countdown display
                if (countdownElement && countdownElement.parentNode) {
                    countdownElement.parentNode.removeChild(countdownElement);
                }
                return;
            }
            
            const mins = Math.floor(totalSeconds / 60);
            const secs = totalSeconds % 60;
            
            countdownElement.innerHTML = `
                <i class="fa fa-clock-o" style="margin-right: 8px;"></i>
                Please wait ${mins} minutes and ${secs} seconds before checking in/out again
            `;
            
            totalSeconds--;
            setTimeout(updateCountdown, 1000);
        };
        
        updateCountdown();
    },

});

PublicWidget.registry.PortalAttendanceHome = PortalAttendanceHome;
PublicWidget.registry.PortalAttendanceHomeControllers = PortalAttendanceHomeControllers;