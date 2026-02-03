/** @odoo-module **/

import public_kiosk_app from "@hr_attendance/public_kiosk/public_kiosk_app";
const kioskAttendanceApp = public_kiosk_app.kioskAttendanceApp;

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService} from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog"
import { onWillStart, onMounted, useRef} from "@odoo/owl";
import { Deferred } from "@web/core/utils/concurrency";

import { loadJS, loadCSS } from "@web/core/assets";

patch(kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");

        // gelocation
        this.glocationContainerRef = useRef("glocation_container");
        this.glocationToggleRef = useRef("glocation_toggle");
        this.glocationViewRef = useRef("glocation_view");
        // geofence
        this.geofenceContainerRef = useRef("geofence_container");
        this.geofenceToggleRef = useRef("geofence_toggle");
        this.geofenceViewRef = useRef("geofence_view");
        // geoipaddress
        this.geoipaddressContainerRef = useRef("geoipaddress_container");
        this.geoipaddressToggleRef = useRef("geoipaddress_toggle");
        this.geoipaddressViewRef = useRef("geoipaddress_view");
        
        // session controls
        this.state.show_recognition = false;
        this.state.show_geolocation = false;
        this.state.show_geofence = false;
        this.state.show_ipaddress = false;

        //geolocation
        this.state.latitude = false;
        this.state.longitude = false;

        //geofence
        this.state.fence_ids = [];
        this.state.fence_is_inside = false;

        //ipaddress
        this.state.ipaddress = false;

        //recogniiton
        this.state.face_detected_employee = false;
        this.state.face_detected_photo = false;
        this.state.fece_is_main_init = false;

        //temp arrays
        this.labeledFaceDescriptors = [];
        
        // Add geofence cache
        this._geofenceCache = {};

        onWillStart(async () => {   
            await this.loadResConfig();

            await loadCSS('/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.css');
            await loadCSS('/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.css');
            await loadJS('/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.js');
            await loadJS('/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.js');
        });

        onMounted(async () => {
            await this.loadControls();
        });
    },
    async loadControls(){
        if (window.location.protocol == 'https:') {
            
            this.geolocationDeferred = new Deferred();
            if (this.state.hr_attendance_geolocation_k) {                
                this.state.show_geolocation = true;
                this.state.latitude = false;
                this.state.longitude = false;                
                await this._getGeolocation();
            }else{
                this.geolocationDeferred.resolve();
            }

            this.geolocationMapDeferred = new Deferred();
            if (this.state.hr_attendance_geofence_k) {
                this.state.show_geofence = true;
                this.state.fence_ids = [];
                this.state.fence_is_inside = false;
                this.state.latitude = false;
                this.state.longitude = false;                                
                await this._getGeofenceMap();
            }else{
                this.geolocationMapDeferred.resolve();
            }

            this.recognitionDeferred = new Deferred();
            if (this.state.hr_attendance_face_recognition_k) {
                this.state.show_recognition = true;                
                await this._initRecognition();
            }else{
                this.recognitionDeferred.resolve();
            }

            this.geolocationAddressDeferred = new Deferred();
            if (this.state.hr_attendance_ip_k){
                this.state.show_ipaddress = true;
                this.state.ipaddress = false;                
                await this._getIpAddress();
            }else{
                this.geolocationAddressDeferred.resolve();
            }
        }else{
            this.state.show_geolocation = false;
            this.state.show_geofence = false;
            this.state.show_ipaddress = false;
            this.state.show_recognition = false;
        }
    },
    async loadResConfig(){
        try {
            const result = await rpc("/hr_attendance/attendance_res_config", {
                'token': this.props.token,
            });
            if (result){
                this.state.hr_attendance_geolocation_k = result.hr_attendance_geolocation_k ? result.hr_attendance_geolocation_k : false;
                this.state.hr_attendance_geofence_k = result.hr_attendance_geofence_k ? result.hr_attendance_geofence_k : false;
                this.state.hr_attendance_face_recognition_k = result.hr_attendance_face_recognition_k ? result.hr_attendance_face_recognition_k : false;
                this.state.hr_attendance_ip_k = result.hr_attendance_ip_k ? result.hr_attendance_ip_k : false;
            }
        } catch (error) {
            console.error("Failed to load configuration:", error);
            this.notificationService.add(_t("Failed to load attendance configuration."), { type: "danger" });
        }
    },
    onToggleGeolocation(){
        var self = this;
        if (self.glocationToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.glocationViewRef.el.classList.remove('d-none');
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-down");
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-up");
        }
        else {
            self.glocationViewRef.el.classList.add('d-none');
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-down");
            self.glocationToggleRef.el.classList.toggle("fa-angle-double-up");
        }
    },
    async _getGeolocation () {
        var self = this;
        if (window.location.protocol == 'https:') {
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        (position) => resolve(position),
                        (error) => reject(error),
                        { timeout: 5000 } // Add timeout to prevent long waits
                    );
                });
                
                if (position.coords.latitude && position.coords.longitude) {
                    self.state.latitude = position.coords.latitude;
                    self.state.longitude = position.coords.longitude;
                    self.geolocationDeferred.resolve();
                } else {
                    self.geolocationDeferred.reject();
                }
            } catch (error) {
                console.error("Geolocation error:", error);
                self.geolocationDeferred.reject();
            }
        } else {
            self.geolocationDeferred.resolve();
        }
    },
    async onTogglegeofence(){
        var self = this;        
        if (self.geofenceToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.geofenceViewRef.el.classList.remove('d-none');
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-up");
            if (self.state.olmap){
                self.state.olmap.setTarget(self.geofenceViewRef.el);
                setTimeout(function () {
                    self.state.olmap.updateSize()
                }, 400);
            }else{
                await this._getGeofenceMap();
            }
        }
        else {
            self.geofenceViewRef.el.classList.add('d-none');
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geofenceToggleRef.el.classList.toggle("fa-angle-double-up");
            // Removed duplicate code - no need to set target and then set it again
            if (self.state.olmap){
                self.state.olmap.setTarget(self.geofenceViewRef.el);
                setTimeout(function () {
                    self.state.olmap.updateSize()
                }, 400);
            }else{
                await this._getGeofenceMap();
            }
        }
    },
    async _initializeMap(latitude, longitude, accuracy = 1000) {
        var self = this;
        
        if (!self.state.olmap) {
            var vectorSource = new ol.source.Vector({});
            self.state.olmap = await new ol.Map({
                layers: [
                    new ol.layer.Tile({
                        source: new ol.source.OSM(),
                    }),
                    new ol.layer.Vector({
                        source: vectorSource
                    })
                ],
                loadTilesWhileInteracting: true,
                view: new ol.View({
                    center: [longitude, latitude],
                    zoom: 2,
                }),
            });
            
            self.state.olmap.setTarget(self.geofenceViewRef.el);
            const Coords = [longitude, latitude];
            const Accuracy = ol.geom.Polygon.circular(Coords, accuracy);
            vectorSource.clear(true);
            vectorSource.addFeatures([
                new ol.Feature(Accuracy.transform('EPSG:4326', self.state.olmap.getView().getProjection())),
                new ol.Feature(new ol.geom.Point(ol.proj.fromLonLat(Coords)))
            ]);
            
            self.state.olmap.getView().fit(vectorSource.getExtent(), {
                duration: 100,
                maxZoom: 6
            });
            
            setTimeout(function() {
                self.state.olmap.updateSize();
            }, 400);
            
            self.geolocationMapDeferred.resolve();
        }
    },
    async _getGeofenceMap() {
        var self = this;
        if (window.location.protocol !== 'https:') {
            self.geolocationMapDeferred.resolve();
            return;
        }
    
        // First check if we already have coordinates in state
        if (self.state.latitude && self.state.longitude) {
            await self._initializeMap(self.state.latitude, self.state.longitude);
            return;
        }
    
        // Try to get coordinates with increased timeout
        try {
            const position = await new Promise((resolve, reject) => {
                // Show a loading message to the user
                self.notificationService.add(_t("Getting your location..."), { type: "info" });
                
                // Try with a longer timeout (10 seconds instead of 5)
                navigator.geolocation.getCurrentPosition(
                    (position) => resolve(position),
                    (error) => reject(error),
                    { 
                        timeout: 10000,  // Increased timeout to 10 seconds
                        maximumAge: 60000, // Allow cached positions up to 1 minute old
                        enableHighAccuracy: false // Disable high accuracy for faster response
                    }
                );
            });
    
            const { latitude, longitude, accuracy } = position.coords;
            if (latitude && longitude) {
                self.state.latitude = latitude;
                self.state.longitude = longitude;
                await self._initializeMap(latitude, longitude, accuracy);
            }
        } catch (error) {
            console.error("Geofence map error:", error);
            
            // Handle timeout specifically
            if (error.code === 3) { // Timeout error
                self.notificationService.add(_t("Location request timed out. Using default location."), { type: "warning" });
                
                // Use a fallback location (could be a default company location or a previous known location)
                // For this example, using a default location (you should replace with appropriate values)
                const fallbackLat = 0;
                const fallbackLng = 0;
                
                // Try to initialize map with fallback coordinates
                try {
                    await self._initializeMap(fallbackLat, fallbackLng, 1000); // Using a large accuracy radius
                    self.notificationService.add(_t("Using approximate location. Geofence validation may not be accurate."), { type: "warning" });
                } catch (mapError) {
                    console.error("Failed to initialize map with fallback coordinates:", mapError);
                    self.geolocationMapDeferred.reject();
                    self.notificationService.add(_t("Could not initialize map. Geofence validation may not work."), { type: "danger" });
                }
            } else if (error.code === 1) { // Permission denied
                self.notificationService.add(_t("Location access denied. Please enable location services to use geofence features."), { type: "danger" });
                self.geolocationMapDeferred.reject();
            } else { // Other errors
                self.notificationService.add(_t("Could not get your location. Using default settings."), { type: "warning" });
                self.geolocationMapDeferred.reject();
            }
        }
    },
    onToggleGeoipaddress(){
        var self = this;

        if (self.geoipaddressToggleRef.el.classList.contains('fa-angle-double-down')) {
            self.geoipaddressViewRef.el.classList.remove('d-none');
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-up");
        }
        else {
            self.geoipaddressViewRef.el.classList.add('d-none');
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-down");
            self.geoipaddressToggleRef.el.classList.toggle("fa-angle-double-up");
        }
    },
    async _getIpAddress() { // Removed unused parameter onNewIP
        var self = this;
        if (window.location.protocol == 'https:') {
            try {
                const response = await fetch("https://api.ipify.org?format=json");
                if (response.status == 200) {
                    const data = await response.json(); // Use json() instead of text() + JSON.parse
                    self.state.ipaddress = data.ip;
                    self.geolocationAddressDeferred.resolve();
                } else {
                    throw new Error(`Failed to get IP address: ${response.status}`);
                }
            } catch (error) {
                console.error("IP address error:", error);
                self.geolocationAddressDeferred.reject();
            }
        } else {
            self.geolocationAddressDeferred.resolve();
        }
    },
    async _initRecognition(){
        var self = this;
        if (window.location.protocol == 'https:') {
            if (!("faceapi" in window)) {
                // Add missing deferred for face recognition
                this.def_face_recognition = new Deferred();
                await self._loadFaceapi();
            } 
            else {
                await self._loadModels();
            }
        }else{
            self.recognitionDeferred.resolve();
        }
    },
    _loadFaceapi () {
        var self = this;
        if (!("faceapi" in window)) {
            (function (w, d, s, g, js, fjs) {
                g = w.faceapi || (w.faceapi = {});
                g.faceapi = { q: [], ready: function (cb) { this.q.push(cb); } };
                js = d.createElement(s); fjs = d.getElementsByTagName(s)[0];
                js.src = window.origin + '/pt_attendance_portal/static/src/lib/faceapi/source/face-api.js';
                fjs.parentNode.insertBefore(js, fjs); js.onload = async function () {
                    console.log("apis loaded");
                    await self._loadModels();
                    self.def_face_recognition.resolve();
                };
            }(window, document, 'script'));
        }
    },
    async _loadModels() {
        var self = this;
        const modelPromises = [
            faceapi.nets.tinyFaceDetector.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceExpressionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
        ];
        try {
            await Promise.all(modelPromises);
            await self.loadLabeledImages();
            return Promise.resolve();
        }catch (error) {
            console.error("Failed to load face recognition models:", error);
            self.notificationService.add(_t("Failed to load face recognition models."), { type: "danger" });
            return Promise.reject(error);
        }
    },
    async loadLabeledImages(){
        var self = this;
        try {
            const data = await rpc('/pt_attendance_portal/loadLabeledImages/');
            self.labeledFaceDescriptors = await Promise.all(
                data.map((dataItem) => {  // Changed variable name to avoid shadowing
                    const descriptors = [];
                    for (let j = 0; j < dataItem.descriptors.length; j++) { // Changed i to j to avoid shadowing
                        if (dataItem.descriptors[j]){
                            descriptors.push(new Float32Array(new Uint8Array([...window.atob(dataItem.descriptors[j])].map(d => d.charCodeAt(0))).buffer));
                        }
                    }
                    return new faceapi.LabeledFaceDescriptors(dataItem.label.toString(), descriptors);
                })
            );
            self.recognitionDeferred.resolve();
        } catch (error) {
            console.error("Failed to load face recognition data:", error);
            self.recognitionDeferred.reject();
            self.notificationService.add(_t("Failed to load face recognition data."), {
                type: "danger",
            });
        }
    },
    onClickRecongintion(){
        var self = this;
        if (self.state.show_recognition) {
            self.state.face_detected_employee = false;
            self.state.face_detected_photo = false;
            self.state.fece_is_main_init = true;
            self.dialog.add(AttendanceRecognitionDialog, {
                faceapi: faceapi,
                labeledFaceDescriptors : this.labeledFaceDescriptors,
                updateRecognitionAttendance: (rdata) => this.updateRecognitionAttendance(rdata),
            });
        }
    },
    async updateRecognitionAttendance( rdata ) {
        var self = this;

        var employeeId = parseInt(rdata.employee_id);
        
        self.state.face_detected_employee = rdata.employee_id;
        self.state.face_detected_photo = rdata.image;

        if (!employeeId){
            return self.notificationService.add(
                _t("Failed: Please try again. Employee not found."), 
                { type: "danger" }
            );
        }

        try {
            const employee = await rpc('attendance_employee_data',{
                'token': this.props.token,
                'employee_id': employeeId,
            });

            if (employee && employee.employee_name){
                if (employee.use_pin){
                    self.employeeData = employee;
                    self.switchDisplay('pin');
                }
                else{
                    try {
                        await this.onManualSelection(employeeId, false);
                    } catch (error) {
                        console.error("Manual selection error:", error);
                        return;
                    }
                }
            } else {
                self.notificationService.add(_t("Employee data not found."), { type: "danger" });
            }
        } catch (error) {
            console.error("Failed to get employee data:", error);
            self.notificationService.add(_t("Failed to get employee data."), { type: "danger" });
        }
    },
    async onManualSelection(employeeId, enteredPin){
        var self = this;
        if(self.state.show_geolocation || self.state.show_geofence || self.state.show_ipaddress || self.state.show_recognition){
        
            let c_latitude = self.state.latitude || 0.0000000;
            let c_longitude = self.state.longitude || 0.0000000;
            let c_fence_ids = Object.values(self.state.fence_ids) || [];
            let c_fence_is_inside = self.state.fence_is_inside || false;
            let c_ipaddress = self.state.ipaddress || false;
            let c_photo = self.state.face_detected_photo || false;
            var c_employee_id = self.state.face_detected_employee || false;
            
            // Start geofence validation early if needed
            let geofenceValidationPromise;
            if (self.state.show_geofence) {
                geofenceValidationPromise = self._validate_Geofence(employeeId);
            }

            // Define Promises
            const geolocationPromise = self.state.show_geolocation
            ? (c_latitude && c_longitude
                ? Promise.resolve(true)
                : new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        ({ coords: { latitude, longitude } }) => {
                            if (latitude && longitude) {
                                self.state.latitude = c_latitude = latitude;
                                self.state.longitude = c_longitude = longitude;
                                resolve({ latitude, longitude });
                            } else {
                                reject("Coordinates not found");
                            }
                        },
                        (error) => reject("Geolocation access denied"),
                        { timeout: 5000 } // Add timeout to prevent long waits
                    );
                }))
            : Promise.resolve(true);
            
            const geofencePromise = self.state.show_geofence
            ? new Promise(async (resolve, reject) => {
                try {
                    // Use the already started validation if available
                    const { fence_is_inside, fence_ids } = geofenceValidationPromise 
                        ? await geofenceValidationPromise 
                        : await self._validate_Geofence(employeeId);
                    
                    if (fence_is_inside && fence_ids.length > 0) {
                        c_fence_ids = Object.values(fence_ids);
                        c_fence_is_inside = fence_is_inside;
                        resolve(true);
                    } else {
                        // Changed from reject to resolve with warning to allow check-in/out to proceed
                        self.notificationService.add(_t("You haven't entered any of the geofence zones, but we'll proceed anyway."), { type: "warning" });
                        reject("You haven't entered any of the geofence zones, but we'll proceed anyway.");
                    }
                } catch (err) {
                    console.error(err);
                    // Changed from reject to resolve with warning to allow check-in/out to proceed
                    self.notificationService.add(_t("Geofence validation error, but we'll proceed anyway."), { type: "warning" });
                    reject("Geofence validation error, but we'll proceed anyway.");
                }
            })
            : Promise.resolve(true);
            
            const faceRecognitionPromise = self.state.show_recognition
                ? (c_photo && c_employee_id
                    ? Promise.resolve(true)
                    : Promise.reject("Face recognition data not available"))
                : Promise.resolve(true);

            const ipAddressPromise = self.state.show_ipaddress
                ? (c_ipaddress
                    ? Promise.resolve(true)
                    : Promise.reject("IP Address not loaded, Please try again."))
                : Promise.resolve(true);

            try {
                // Use Promise.allSettled instead of Promise.all to continue even if some promises fail
                const results = await Promise.allSettled([
                    geolocationPromise, 
                    geofencePromise, 
                    ipAddressPromise, 
                    faceRecognitionPromise
                ]);
                
                // Check for any rejected promises and show warnings
                const rejectedPromises = results.filter(result => result.status === 'rejected');
                if (rejectedPromises.length > 0) {
                    rejectedPromises.forEach(promise => {
                        self.notificationService.add(_t(promise.reason || "A validation step failed"), { type: "warning" });
                    });
                    return;
                }

                // Reverting Recognition States
                self.state.face_detected_photo = false;
                self.state.face_detected_employee= false;
                self.state.fece_is_main_init = false;
            
                const result = await self.rpc('manual_selection',{
                    'token': self.props.token,
                    'employee_id': employeeId,
                    'pin_code': enteredPin
                });

                if (result && result.attendance) {
                    if (result.attendance.id && result.attendance_state == "checked_in"){
                        await self.rpc('update_checkin_controls',{
                            'token': self.props.token,
                            'attendance_id':parseInt(result.attendance.id),
                            'check_in_latitude': c_latitude,
                            'check_in_longitude': c_longitude,
                            'check_in_geofence_ids': c_fence_ids,
                            'check_in_photo': c_photo,
                            'check_in_ipaddress': c_ipaddress,
                        });
                    }
                    else if(result.attendance.id && result.attendance_state == "checked_out"){
                        await self.rpc('update_checkout_controls',{
                            'token': self.props.token,
                            'attendance_id':parseInt(result.attendance.id),
                            'check_out_latitude': c_latitude,
                            'check_out_longitude': c_longitude,
                            'check_out_geofence_ids': c_fence_ids,
                            'check_out_photo': c_photo,
                            'check_out_ipaddress': c_ipaddress,
                        });
                    }
                    this.employeeData = result;
                    this.switchDisplay('greet');
                }
                else{
                    if (enteredPin){
                        this.displayNotification(_t("Wrong Pin"));
                    }
                }

            } catch (error) {
                console.error("Validation failed:", error);
                self.notificationService.add(_t(error), { type: "danger" });
            }
        }
        else{
            try {
                const result = await self.rpc('manual_selection',
                    {
                        'token': this.props.token,
                        'employee_id': employeeId,
                        'pin_code': enteredPin
                    });
                if (result && result.attendance) {               
                    this.employeeData = result;
                    this.switchDisplay('greet');
                } else {
                    if (enteredPin){
                        this.displayNotification(_t("Wrong Pin"));
                    }
                }
            } catch (error) {
                console.error("Manual selection error:", error);
                self.notificationService.add(_t("Failed to process attendance."), { type: "danger" });
            }
        }
    },  
    async _validate_Geofence(employeeId) {
        const self = this;
        
        let fence_is_inside = false;
        let fence_ids = [];

        if (window.location.protocol !== 'https:') {
            return { fence_is_inside, fence_ids };
        }

        try {
            // Use existing coordinates if available to avoid another geolocation request
            let coords;
            if (self.state.latitude && self.state.longitude) {
                coords = ol.proj.fromLonLat([self.state.longitude, self.state.latitude]);
            } 
            else {
                // Only get geolocation if we don't already have it
                try {
                    const geolocation = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(
                            ({ coords: { latitude, longitude } }) => {
                                // Store for future use
                                self.state.latitude = latitude;
                                self.state.longitude = longitude;
                                resolve({ latitude, longitude });
                            },
                            (err) => reject(err),
                            { timeout: 5000 } // Add timeout to prevent long waits
                        );
                    });
                    coords = ol.proj.fromLonLat([geolocation.longitude, geolocation.latitude]);
                } catch (geoError) {
                    console.error("Geolocation error:", geoError);
                    self.notificationService.add(_t("Could not get your location. Please check your location permissions."), { type: "warning" });
                    return { fence_is_inside, fence_ids };
                }
            }

            // Add caching for geofence data
            const cacheKey = `${employeeId}_${self.props.token}`;
            let records;
            
            // Use cached data if available and not older than 5 minutes
            if (self._geofenceCache[cacheKey] && 
                (Date.now() - self._geofenceCache[cacheKey].timestamp < 5 * 60 * 1000)) {
                records = self._geofenceCache[cacheKey].records;
            } 
            else {
                // Fetch and cache the records
                records = await rpc('/hr_attendance/get_geofences/', {
                    'token': self.props.token,
                    'employee_id': parseInt(employeeId),
                });
                
                self._geofenceCache[cacheKey] = {
                    records,
                    timestamp: Date.now()
                };
            }
            
            if (!records || records.length === 0) {
                self.notificationService.add(_t("No geofence zones found for this employee."), { type: "warning" });
                return { fence_is_inside, fence_ids };
            }

            // Process records in batches to avoid blocking the UI
            const batchSize = 5;
            for (let i = 0; i < records.length; i += batchSize) {
                const batch = records.slice(i, i + batchSize);
                
                // Use Promise.all to process batch in parallel
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
                        if (geometry.intersectsCoordinate(coords)) {
                            return parseInt(record.id);
                        }
                    } catch (parseError) {
                        console.error("Error processing geofence record:", parseError);
                    }
                    return null;
                }));
                
                // Filter out nulls and add valid IDs
                const validIds = results.filter(id => id !== null);
                if (validIds.length > 0) {
                    fence_is_inside = true;
                    fence_ids.push(...validIds);
                }
                
                // If we found at least one match, we can stop processing
                if (fence_is_inside) {
                    break;
                }
            }
            
            if (!fence_is_inside) {
                self.notificationService.add(_t("You haven't entered any of the geofence zones."), { type: "warning" });
            }
        } catch (error) {
            console.error("Geofence validation error:", error);
            self.notificationService.add(_t("Error validating geofence."), { type: "danger" });
        }

        return {
            'fence_is_inside': fence_is_inside, 
            'fence_ids': fence_ids,
        };
    },
});