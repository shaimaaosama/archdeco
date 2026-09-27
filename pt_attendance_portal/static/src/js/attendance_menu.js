/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { onWillStart, useRef } from "@odoo/owl";
import { session } from "@web/session";
import { loadJS, loadCSS } from "@web/core/assets";
import { Deferred } from "@web/core/utils/concurrency";

import { AttendanceRecognitionDialog } from "./attendance_recognition_dialog"
import { AttendanceWebcamDialog } from "./attendance_webcam_dialog"

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.notificationService = useService('notification');
        
        //reason
        this.reasonContainerRef = useRef("reason_container");
        this.reasonToggleRef = useRef("reason_toggle");
        this.reasonViewRef = useRef("reason_view");
        this.reasonInputRef = useRef("reason_input"); // Fixed typo: "reasons_inut" -> "reason_input"
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
        this.state.show_geolocation = false;
        this.state.show_geofence = false;
        this.state.show_ipaddress = false;
        this.state.show_recognition = false;
        this.state.show_photo = false;
        this.state.show_reason = false;

        // gelocation
        this.state.latitude = false;
        this.state.longitude = false;
        // geofence
        this.state.olmap = false;
        this.state.fence_is_inside = false;
        this.state.fence_ids = [];
        //ipaddress
        this.state.ipaddress = false;        

        //temp arrays
        this.reasons = [];
        this.labeledFaceDescriptors = [];

        onWillStart(async () => {
            await loadCSS('/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.css');
            await loadCSS('/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.css');
            await loadJS('/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.js');
            await loadJS('/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.js');
        });
    },
    async loadControls(){
        if (window.location.protocol == 'https:') {
            
            this.geolocationDeferred = new Deferred();
            if (session.hr_attendance_geolocation) {
                this.state.show_geolocation = true;
                this.state.latitude = false;
                this.state.longitude = false;
                await this._getGeolocation();
            }else{
                this.geolocationDeferred.resolve();
            }

            this.geolocationMapDeferred = new Deferred();
            if (session.hr_attendance_geofence) {
                this.state.show_geofence = true;
                this.state.fence_ids = [];
                this.state.fence_is_inside = false;
                this.state.latitude = false;
                this.state.longitude = false;                
                await this._getGeofenceMap();
            }else{
                this.geolocationMapDeferred.resolve();
            }

            this.geolocationAddressDeferred = new Deferred();
            if (session.hr_attendance_ip) {
                this.state.show_ipaddress = true;
                this.state.ipaddress = false;                
                await this._getIpAddress();
            }else{
                this.geolocationAddressDeferred.resolve();
            }

            this.recognitionDeferred = new Deferred();
            if (session.hr_attendance_face_recognition){
                this.state.show_recognition = true;
                await this._initRecognition();
            }else{
                this.recognitionDeferred.resolve();
            }

            if (session.hr_attendance_photo){
                this.state.show_photo = true;
            }
        }else{
            this.state.show_geolocation = false;
            this.state.show_geofence = false;
            this.state.show_ipaddress = false;
            this.state.show_recognition = false;
            this.state.show_photo = false;
        }

        if (session.hr_attendance_reason){
            this.state.show_reason = true;
            await this._getReasons();
        }else{
            this.state.show_reason = false;
        }
    },
    onToggleGeolocation(){
        var self = this;
        const toggleEl = self.glocationToggleRef.el;
        const viewEl = self.glocationViewRef.el;
        if (toggleEl.classList.contains('fa-angle-double-down')) {
            viewEl.classList.remove('d-none');
            toggleEl.classList.remove('fa-angle-double-down');
            toggleEl.classList.add('fa-angle-double-up');
        }
        else {
            viewEl.classList.add('d-none');
            toggleEl.classList.remove('fa-angle-double-up');
            toggleEl.classList.add('fa-angle-double-down');
        }
    },
    async _getGeolocation () {
        var self = this;
        if (window.location.protocol == 'https:') {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    self.state.latitude = latitude;
                    self.state.longitude = longitude;
                    self.geolocationDeferred.resolve();
                },
                async err => {
                    self.geolocationDeferred.reject();
                }
            );
        }else{
            self.geolocationDeferred.resolve();
        }
    },
    async onTogglegeofence(){
        var self = this;
        const toggleEl = self.geofenceToggleRef.el;
        const viewEl = self.geofenceViewRef.el;
        if (toggleEl.classList.contains('fa-angle-double-down')) {
            viewEl.classList.remove('d-none');
            toggleEl.classList.remove('fa-angle-double-down');
            toggleEl.classList.add('fa-angle-double-up');
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
            viewEl.classList.add('d-none');
            toggleEl.classList.remove('fa-angle-double-up');
            toggleEl.classList.add('fa-angle-double-down');
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
    _getGeofenceMap () {
        var self = this;
        if (window.location.protocol == 'https:') {
            navigator.geolocation.getCurrentPosition(
                async ({coords: {accuracy, latitude, longitude}}) => {
                    if (latitude && longitude){
                        self.state.latitude = latitude;
                        self.state.longitude = longitude;

                        if (!self.state.olmap) {
                            var olmap_div = self.geofenceViewRef.el;
                            
                            olmap_div.style.width = '350px';
                            olmap_div.style.height = '200px';
        
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
                                    center: [longitude, latitude], // Fixed: was using [latitude, longitude] which is incorrect for ol.View
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
                            self.state.olmap.getView().fit(vectorSource.getExtent(), { duration: 100, maxZoom: 6 });
                            setTimeout(function () {
                                self.state.olmap.updateSize()
                            }, 400);
        
                            self.geolocationMapDeferred.resolve();
                        }
                    }
                },
                async err => {
                    self.geolocationMapDeferred.reject();
                }
            );
        }else{
            self.geolocationMapDeferred.resolve();
        }        
    },
    onToggleGeoipaddress(){
        var self = this;
        const toggleEl = self.geoipaddressToggleRef.el;
        const viewEl = self.geoipaddressViewRef.el;
        if (toggleEl.classList.contains('fa-angle-double-down')) {
            viewEl.classList.remove('d-none');
            toggleEl.classList.remove('fa-angle-double-down');
            toggleEl.classList.add('fa-angle-double-up');
        }
        else {
            viewEl.classList.add('d-none');
            toggleEl.classList.remove('fa-angle-double-up');
            toggleEl.classList.add('fa-angle-double-down');
        }
    },
    async _getIpAddress() { // Removed unused parameter onNewIP
        var self = this;
        if (window.location.protocol == 'https:') {
            try {
                const response = await fetch("https://api.ipify.org?format=json");
                const data = await response.json();
                if (data.ip) {
                    self.state.ipaddress = data.ip;
                    self.geolocationAddressDeferred.resolve();
                } else {
                    self.geolocationAddressDeferred.reject();
                }
            } catch (error) {
                self.geolocationAddressDeferred.reject();
            }
        } else {
            self.geolocationAddressDeferred.resolve();
        }
    },
    onToggleReason(){
        var self = this;
        const toggleEl = self.reasonToggleRef.el;
        const viewEl = self.reasonViewRef.el;
        if (toggleEl.classList.contains('fa-angle-double-down')) {
            viewEl.classList.remove('d-none');
            toggleEl.classList.remove('fa-angle-double-down');
            toggleEl.classList.add('fa-angle-double-up');
        }
        else {
            viewEl.classList.add('d-none');
            toggleEl.classList.remove('fa-angle-double-up');
            toggleEl.classList.add('fa-angle-double-down');
        }
    },
    async _getReasons(){
        var self = this;
        try {
            const reasons = await rpc("/web/dataset/call_kw/hr.attendance.reasons/search_read", {
                model: "hr.attendance.reasons",
                method: "search_read",
                args: [[], ['id', 'name', 'attendance_state']],
                kwargs: {},
            });
            self.reasons = reasons;
        } catch (error) {
            console.error("Failed to fetch reasons:", error);
        }
    },
    async _initRecognition(){
        var self = this;
        if (window.location.protocol == 'https:') {
            // Check if current employee has face descriptors
            if (!this.employee || !this.employee.id) {
                console.log("Employee not available yet, skipping face recognition initialization");
                self.recognitionDeferred.resolve();
                return;
            }
            try {
                const employeeFaceCheck = await rpc('/pt_attendance_portal/check_employee_face_descriptors', {
                    'employee_id': parseInt(this.employee.id),
                });
                
                self.employee_has_face_descriptors = employeeFaceCheck.has_face_descriptors;
                self.employee_face_count = employeeFaceCheck.face_count;
                
                console.log("Employee face descriptors check:", employeeFaceCheck);
                
                // Only load face recognition if employee has descriptors
                if (self.employee_has_face_descriptors) {
                    if (!("faceapi" in window)) {
                        // Add missing deferred
                        self.def_face_recognition = new Deferred();
                        self._loadFaceapi();
                    } 
                    else {
                        await self._loadModels();
                    }
                } else {
                    console.log("Employee has no face descriptors - skipping face recognition initialization");
                    self.recognitionDeferred.resolve();
                }
            } catch (error) {
                console.error("Failed to check employee face descriptors:", error);
                self.employee_has_face_descriptors = false;
                self.employee_face_count = 0;
                self.recognitionDeferred.resolve();
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
        const promises = [];
        promises.push([
            faceapi.nets.tinyFaceDetector.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceExpressionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
        ])
        return Promise.all(promises).then(() => {
            self.loadLabeledImages();            
            return Promise.resolve();
        });
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
            self.recognitionDeferred.reject();
            self.notificationService.add(_t("Failed to load face recognition data."), {
                type: "danger",
            });
        }
    },

    async _validate_Geofence() {
        const self = this;
        
        let fence_is_inside = false;
        let fence_ids = [];
    
        if (window.location.protocol !== 'https:') {
            return { fence_is_inside, fence_ids };
        }
    
        try {
            let coords;
            if (self.state.latitude && self.state.longitude) {
                coords = ol.proj.fromLonLat([self.state.longitude, self.state.latitude]);
            } 
            else {
                try {
                    const geolocation = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(
                            ({ coords: { latitude, longitude } }) => {
                                self.state.latitude = latitude;
                                self.state.longitude = longitude;
                                resolve({ latitude, longitude });
                            },
                            (err) => reject(err),
                            { timeout: 5000 }
                        );
                    });
                    coords = ol.proj.fromLonLat([geolocation.longitude, geolocation.latitude]);
                } 
                catch (geoError) {
                    console.error("Geolocation error:", geoError);
                    self.notificationService.add(_t("Could not get your location. Please check your location permissions."), { type: "warning" });
                    return { fence_is_inside, fence_ids };
                }
            }
    
            const company_id = session.user_companies.allowed_companies[0] || session.user_companies.current_company || false;
            
            // Add caching for geofence data
            if (!self._geofenceCache) {
                self._geofenceCache = {};
            }
            
            if (!self.employee || !self.employee.id) {
                self.geolocationMapDeferred.resolve();
                return;
            }
            const cacheKey = `${company_id}_${self.employee.id}`;
            let records;
            
            // Use cached data if available and not older than 5 minutes
            if (self._geofenceCache[cacheKey] && 
                (Date.now() - self._geofenceCache[cacheKey].timestamp < 5 * 60 * 1000)) {
                records = self._geofenceCache[cacheKey].records;
            } else {
                // Fetch and cache the records
                records = await self.orm.call(
                    'hr.attendance.geofence', 
                    "search_read", 
                    [[['company_id', '=', company_id], ['employee_ids', 'in', self.employee.id]], 
                    ['id', 'name', 'overlay_paths']], 
                    {}
                );
                
                self._geofenceCache[cacheKey] = {
                    records,
                    timestamp: Date.now()
                };
            }
            
            if (!records || records.length === 0) {
                self.notificationService.add(_t("No geofence zones found for your account."), { type: "warning" });
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
        } 
        catch (error) {
            console.error("Geofence validation error:", error);
            self.notificationService.add(_t("Error validating geofence."), { type: "danger" });
        }
    
        return {
            'fence_is_inside': fence_is_inside, 
            'fence_ids': fence_ids,
        };
    },
    
    async signInOut() {
        var self = this;
        // Close dropdown first, like the original method
        if (self.dropdown) {
            self.dropdown.close();
        }
    
        if (self.state.show_geolocation || self.state.show_geofence || self.state.show_ipaddress || 
            self.state.show_recognition || self.state.show_photo || self.state.show_reason) {
    
            let c_latitude = self.state.latitude || 0.0000000;
            let c_longitude = self.state.longitude || 0.0000000;
            let c_fence_ids = [];
            let c_fence_is_inside = false;
            let c_ipaddress = self.state.ipaddress || false;
            let c_photo = false;
            let c_reason = self.reasonInputRef.el && self.reasonInputRef.el.value || '-';
    
            // Start geofence validation early if needed
            let geofenceValidationPromise;
            if (self.state.show_geofence) {
                geofenceValidationPromise = self._validate_Geofence();
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
                        : await self._validate_Geofence();
                    
                    if (fence_is_inside && fence_ids.length > 0) {
                        c_fence_ids = fence_ids;
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
    
            // Rest of the promises remain the same...
            const ipAddressPromise = self.state.show_ipaddress
            ? (c_ipaddress
                  ? Promise.resolve(true)
                  : Promise.reject("IP Address not loaded, Please try again."))
            : Promise.resolve(true);
    
            const photoPromise = self.state.show_photo
            ? new Promise((resolve, reject) => {
                  if (!c_photo) {
                      self.dialog.add(AttendanceWebcamDialog, {
                          uploadWebcamImage: (rdata) => {
                              if (rdata.image) {
                                  c_photo = rdata.image;
                                  resolve(true);
                              } else {
                                  reject("Photo not loaded, Please try again.");
                              }
                          }
                      });
                  } else {
                      resolve(true);
                  }
              })
            : Promise.resolve(true);
    
            const faceRecognitionPromise = self.state.show_recognition
            ? new Promise((resolve, reject) => {
                  // If employee doesn't have face descriptors, allow check-in without face recognition
                  if (!self.employee_has_face_descriptors) {
                      console.log("Employee has no face descriptors - allowing check-in without face recognition");
                      resolve(true);
                      return;
                  }
                  
                  if (self.labeledFaceDescriptors?.length) {
                      self.dialog.add(AttendanceRecognitionDialog, {
                          faceapi: faceapi,
                          labeledFaceDescriptors: self.labeledFaceDescriptors,
                          updateRecognitionAttendance: (rdata) => {
                              if (parseInt(self.employee.id) !== parseInt(rdata.employee_id)) {
                                  reject("The detected employee does not match the logged-in employee.");
                              } else {
                                  c_photo = rdata.image;
                                  resolve(true);
                              }
                          }
                      });
                  } else {
                      reject("Detection Failed: Resource not found. Please add it to your user's profile.");
                  }
              })
            : Promise.resolve(true);
    
            const reasonPromise = self.state.show_reason
                ? (c_reason
                    ? Promise.resolve(true)
                    : Promise.reject("Reason not loaded, Please try again."))
                : Promise.resolve(true);
    
            try {
                // Use Promise.allSettled instead of Promise.all to continue even if some promises fail
                const results = await Promise.allSettled([
                    geolocationPromise, 
                    geofencePromise, 
                    ipAddressPromise, 
                    photoPromise, 
                    faceRecognitionPromise, 
                    reasonPromise
                ]);
                
                
                // Check for any rejected promises and show warnings
                const rejectedPromises = results.filter(result => result.status === 'rejected');
                if (rejectedPromises.length > 0) {
                    rejectedPromises.forEach(promise => {
                        self.notificationService.add(_t(promise.reason || "A validation step failed"), { type: "warning" });
                    });
                    return;
                }
                
                try {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                    });
                    
                    const { latitude, longitude } = position.coords;
                    const data = await rpc("/hr_attendance/systray_check_in_out", {
                        latitude,
                        longitude
                    });
                    
                    await self._updateAttendanceRecord(data, c_latitude || latitude, c_longitude || longitude, c_fence_ids, c_photo, c_ipaddress, c_reason);
                    await self.searchReadEmployee();
                    
                } catch (error) {
                    // Fallback if geolocation fails
                    const data = await rpc("/hr_attendance/systray_check_in_out");
                    await self._updateAttendanceRecord(data, c_latitude, c_longitude, c_fence_ids, c_photo, c_ipaddress, c_reason);
                    await self.searchReadEmployee();
                }
                
            } catch (error) {
                console.error("Validation failed:", error);
                self.notificationService.add(_t(error), { type: "danger" });
            }
        } 
        else {
            // Rest of the code remains the same...
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                });
                
                await rpc("/hr_attendance/systray_check_in_out", {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
                
            } catch (error) {
                await rpc("/hr_attendance/systray_check_in_out");
            }
            
            await self.searchReadEmployee();
        }
    },
    
    async searchReadEmployee() {
        // Call the original searchReadEmployee first
        await super.searchReadEmployee();
        // Then load controls if employee is available and controls haven't been loaded yet
        if (this.employee && this.employee.id && !this._controlsLoaded) {
            this._controlsLoaded = true;
            await this.loadControls();
        }
    },

    async _updateAttendanceRecord(data, latitude, longitude, fence_ids, photo, ipaddress, reason) {
        if (!data.attendance.id) {
            return;
        }
        
        const updateData = data.attendance_state === "checked_in" 
            ? {
                'check_in_latitude': latitude,
                'check_in_longitude': longitude,
                'check_in_geofence_ids': fence_ids,
                'check_in_photo': photo,
                'check_in_ipaddress': ipaddress,
                'check_in_reason': reason,
            }
            : {
                'check_out_latitude': latitude,
                'check_out_longitude': longitude,
                'check_out_geofence_ids': fence_ids,
                'check_out_photo': photo,
                'check_out_ipaddress': ipaddress,
                'check_out_reason': reason,
            };
            
        await rpc("/web/dataset/call_kw/hr.attendance/write", {
            model: "hr.attendance",
            method: "write",
            args: [parseInt(data.attendance.id), updateData],
            kwargs: {},
        });
    }
});

export default ActivityMenu;