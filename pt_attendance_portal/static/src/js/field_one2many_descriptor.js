/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { X2ManyFieldDialog } from "@web/views/fields/relational_utils";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(X2ManyFieldDialog.prototype, {
    setup() {
        super.setup();
        this.notificationService = useService("notification");
    },
    
    showLoadingOverlay() {
        // Try multiple ways to find the dialog
        let dialog = null;
        
        // Method 1: Try from this.el
        if (this.el) {
            dialog = this.el.closest('.modal, .o_dialog, [role="dialog"], .o-dialog');
        }
        
        // Method 2: Try to find the active dialog in the DOM
        if (!dialog) {
            dialog = document.querySelector('.modal.show, .o_dialog, [role="dialog"]:not([hidden]), .o-dialog');
        }
        
        // Method 3: Try to find any dialog that contains our form
        if (!dialog) {
            const form = document.querySelector('form[data-model="hr.employee.faces"]');
            if (form) {
                dialog = form.closest('.modal, .o_dialog, [role="dialog"], .o-dialog');
            }
        }
        
        if (dialog) {
            // Disable all buttons in the dialog
            const buttons = dialog.querySelectorAll('button, .btn, [type="button"], [type="submit"]');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
                btn.setAttribute('data-face-recognition-disabled', 'true');
            });
            
            // Find the image container - try multiple selectors
            let imageContainer = dialog.querySelector('#face_image, .o_field_image, [name="image"], .o_website_sale_image_modal_container');
            
            // If not found, try to find the image field wrapper
            if (!imageContainer) {
                const imageField = dialog.querySelector('field[name="image"]');
                if (imageField) {
                    imageContainer = imageField.closest('.o_field_widget, .col, div');
                }
            }
            
            // Use image container if found, otherwise use dialog
            const container = imageContainer || dialog;
            
            // Create loading overlay if it doesn't exist
            let overlay = container.querySelector('.face-recognition-loading-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'face-recognition-loading-overlay';
                overlay.innerHTML = `
                    <div class="face-recognition-spinner-container">
                        <div class="face-recognition-spinner"></div>
                        <div class="face-recognition-loading-text">Generating face descriptor...</div>
                    </div>
                `;
                // Ensure container has relative positioning
                const currentPosition = window.getComputedStyle(container).position;
                if (currentPosition === 'static') {
                    container.style.position = 'relative';
                }
                container.appendChild(overlay);
            }
            overlay.style.display = 'flex';
            // Smooth fade transition for dialog with modern easing
            dialog.style.transition = 'opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1), filter 0.35s cubic-bezier(0.16, 1, 0.3, 1)';
            dialog.style.opacity = '0.7';
            dialog.style.filter = 'blur(2px)';
            dialog.style.pointerEvents = 'none';
            dialog.style.userSelect = 'none';
        } else {
            console.warn('Could not find dialog element for loading overlay');
        }
    },
    
    hideLoadingOverlay() {
        // Try multiple ways to find the dialog
        let dialog = null;
        
        if (this.el) {
            dialog = this.el.closest('.modal, .o_dialog, [role="dialog"], .o-dialog');
        }
        
        if (!dialog) {
            dialog = document.querySelector('.modal.show, .o_dialog, [role="dialog"]:not([hidden]), .o-dialog');
        }
        
        if (!dialog) {
            const form = document.querySelector('form[data-model="hr.employee.faces"]');
            if (form) {
                dialog = form.closest('.modal, .o_dialog, [role="dialog"], .o-dialog');
            }
        }
        
        if (dialog) {
            // Re-enable all buttons
            const buttons = dialog.querySelectorAll('[data-face-recognition-disabled="true"]');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = '';
                btn.removeAttribute('data-face-recognition-disabled');
            });
            
            // Find overlay in image container or dialog
            let imageContainer = dialog.querySelector('#face_image, .o_field_image, [name="image"], .o_website_sale_image_modal_container');
            if (!imageContainer) {
                const imageField = dialog.querySelector('field[name="image"]');
                if (imageField) {
                    imageContainer = imageField.closest('.o_field_widget, .col, div');
                }
            }
            const container = imageContainer || dialog;
            
            const overlay = container.querySelector('.face-recognition-loading-overlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
            // Smooth fade back with modern easing
            dialog.style.transition = 'opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1), filter 0.35s cubic-bezier(0.16, 1, 0.3, 1)';
            dialog.style.opacity = '1';
            dialog.style.filter = 'blur(0px)';
            dialog.style.pointerEvents = 'auto';
            dialog.style.userSelect = 'auto';
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
                    console.log("Face API loaded for descriptor generation");
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

    load_models: async function(){
        var self = this;
        // First load face-api.js if not already loaded
        await self._loadFaceapi();
        
        const promises = [];
        promises.push(
            faceapi.nets.tinyFaceDetector.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights'),
            faceapi.nets.faceExpressionNet.loadFromUri('/pt_attendance_portal/static/src/lib/faceapi/weights')
        );
        return Promise.all(promises);
    },

    async save({ saveAndNew }) {
        if(this.record.resModel === 'hr.employee.faces'){
            var self = this;
            var imageData = this.record.data.image || false;            
            if (imageData){
                // Show loading overlay immediately
                // Use setTimeout to ensure DOM is ready
                setTimeout(() => {
                    self.showLoadingOverlay();
                }, 10);
                
                try {
                    // Use image data directly from record instead of finding DOM element
                    await self.getDescriptorFromData(imageData);
                } catch (error) {
                    self.hideLoadingOverlay();
                    throw error;
                }
            } else {
                return super.save({ saveAndNew });
            }
        }else{
            return super.save({ saveAndNew });
        }
    },

    async getDescriptorFromData(imageData){
        var self = this;
        try {
            await self.load_models();
            var has_Detection_model = self.isFaceDetectionModelLoaded();
            var has_Recognition_model = self.isFaceRecognitionModelLoaded();
            var has_Landmark_model = self.isFaceLandmarkModelLoaded();            
            
            if (has_Detection_model && has_Recognition_model && has_Landmark_model){
                // Create image element from base64 data
                var img = document.createElement('img');
                
                // Handle both base64 string and data URI formats
                if (typeof imageData === 'string') {
                    // If it's already a data URI, use it directly
                    if (imageData.startsWith('data:image')) {
                        img.src = imageData;
                    } else {
                        // Otherwise, assume it's base64 and create data URI
                        // Try common image formats
                        let mimeType = 'image/jpeg'; // default
                        // Check if it looks like PNG (starts with iVBORw0KGgo)
                        if (imageData.substring(0, 22) === 'iVBORw0KGgoAAAANSUhEUgAA') {
                            mimeType = 'image/png';
                        }
                        img.src = `data:${mimeType};base64,${imageData}`;
                    }
                } else {
                    console.warn('Unexpected image data format:', typeof imageData);
                    return super.save({ saveAndNew: false });
                }
                
                // Wait for image to load
                await new Promise((resolve, reject) => {
                    if (img.complete) {
                        resolve();
                    } else {
                        img.onload = resolve;
                        img.onerror = () => {
                            console.error('Failed to load image for face detection');
                            reject(new Error('Image load failed'));
                        };
                    }
                });
                
                // SsdMobilenetv1Options //Using tinyFaceDetector
                const result = await faceapi.detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
                    .withFaceLandmarks()
                    .withFaceDescriptor();
                    
                if (result && result.descriptor){
                    var descriptor = self.formatDescriptor(result.descriptor);
                    await self.updateDescriptor(descriptor);
                    // Success notification will be shown in updateDescriptor
                } else {
                    console.warn('No face detected in image');
                    self.hideLoadingOverlay();
                    self.notificationService.add(
                        _t("No face detected in the image. Please use a clear photo with a visible face."),
                        { type: "warning", title: _t("Face Detection Failed") }
                    );
                    // Still save the record even if no face is detected
                    return super.save({ saveAndNew: false });
                }
            } else {
                // Retry after a short delay if models aren't loaded yet
                setTimeout(() => self.getDescriptorFromData(imageData), 500);
            }
        } catch (error) {
            console.error('Error in getDescriptorFromData:', error);
            self.hideLoadingOverlay();
            self.notificationService.add(
                _t("Failed to generate face descriptor. Please try again or contact support."),
                { type: "danger", title: _t("Error") }
            );
            // Fall back to normal save if face recognition fails
            return super.save({ saveAndNew: false });
        }
    },
    async updateDescriptor(descriptor){
        var self = this;
        await this.record.update({
            'descriptor': descriptor
        });
        if (await this.record.checkValidity()) {
            const saved = (await this.props.save(this.record, {})) || this.record;
            self.hideLoadingOverlay();
            self.notificationService.add(
                _t("Face descriptor generated successfully!"),
                { type: "success", title: _t("Success") }
            );
            // Small delay to show notification before closing
            setTimeout(() => {
                this.props.close();
            }, 500);
            return true;
        } else {
            console.error('Record validation failed');
            self.hideLoadingOverlay();
            self.notificationService.add(
                _t("Failed to save face descriptor. Please try again."),
                { type: "danger", title: _t("Validation Error") }
            );
            return false;
        }
    },
    formatDescriptor(descriptor) {
        var self = this;
        let result = window.btoa(String.fromCharCode(...(new Uint8Array(descriptor.buffer))));
        return result;
    },
    getCurrentFaceDetectionNet() {
        var self = this;
        // ssdMobilenetv1 //Using tinyFaceDetector
        return faceapi.nets.tinyFaceDetector;
    },

    isFaceDetectionModelLoaded() {
        var self = this;
        return !!self.getCurrentFaceDetectionNet().params
    },

    getCurrentFaceRecognitionNet () {
        var self = this;
        return faceapi.nets.faceRecognitionNet;
    },

    isFaceRecognitionModelLoaded() {
        var self = this;
        return !!self.getCurrentFaceRecognitionNet().params
    },

    getCurrentFaceLandmarkNet() {
        var self = this;
        return faceapi.nets.faceLandmark68Net;
    },

    isFaceLandmarkModelLoaded() {
        var self = this;
        return !!self.getCurrentFaceLandmarkNet().params
    },
    
});