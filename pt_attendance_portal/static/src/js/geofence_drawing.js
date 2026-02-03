/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { loadJS, loadCSS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillStart, onMounted, useEffect, useRef } from "@odoo/owl";

export class GeofenceDrawing extends Component {
    static template = "pt_attendance_portal.GeofenceDrawingView";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.mapContainerRef = useRef("mapContainer");

        this.olmap = null;
        this.isDrawingEnabled = false;
        this.circleFeature = null; // Track circle feature created from input fields

        if (!this.props.record.data[this.props.name]) {
            this.props.record.data[this.props.name]= 'Empty';
        }

        useEffect(
            () => {
                this.olmap = new ol.Map({
                    layers: [
                        new ol.layer.Tile({
                            source: new ol.source.OSM(),
                        })],
                    view: new ol.View({
                        center: ol.proj.fromLonLat([0, 0]),
                        zoom: 0,
                    }),
                });
                this.olmap.setTarget(this.mapContainerRef.el);
                this.olmap.updateSize();
                if (this.olmap){
                    this.addLayerVector();
                }
            },
            () => []
        );
        useEffect(() => {
            this.updateMap();
        });
        
        // Watch for changes in input fields
        useEffect(() => {
            this.watchInputFields();
        }, () => [
            this.props.record.data.input_latitude,
            this.props.record.data.input_longitude,
            this.props.record.data.input_radius
        ]);

        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    async onWillStart() {
        await loadCSS('/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.css');
        await loadCSS('/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.css');
        await loadJS('/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.js');
        await loadJS('/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.js');
    }

    onMounted() {
        if(this.olmap){
            this.olmap.updateSize();
        }
    }

    addLayerVector(){
        if (!this.vectorSource) {
            this.vectorSource = new ol.source.Vector();
        }
        if (!this.vectorLayer) {
            this.vectorLayer = new ol.layer.Vector({
                source: this.vectorSource,
                name: 'vectorSource',
                style: new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: 'rgb(255 235 59 / 62%)',
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#ffc107',
                        width: 2,
                    }),
                    image: new ol.style.Circle({
                        radius: 7,
                        fill: new ol.style.Fill({
                            color: '#ffc107',
                        }),
                    }),
                }),
            });
            this.olmap.addLayer(this.vectorLayer);
        }
        if (this.props.record.data[this.props.name] && this.props.record.data[this.props.name] != 'Empty') {                
            var readFeatures = new ol.format.GeoJSON().readFeatures(this.props.record.data[this.props.name]);
            this.vectorSource.addFeatures(readFeatures);
            this.vectorSource.getFeatures().forEach((feature)=>{
                feature.setStyle(
                    new ol.style.Style({
                        fill: new ol.style.Fill({
                            color: 'rgb(255 235 59 / 62%)',
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#ffc107',
                            width: 2,
                        }),
                        image: new ol.style.Circle({
                            radius: 7,
                            fill: new ol.style.Fill({
                                color: '#ffc107',
                            }),
                        }),
                    })
                );
            });
        }
    }

    updateMap() {
        this.addPolygonDrawingControl();
        this.addPolygonClearControl();
    }

    addPolygonDrawingControl(){
        var buttonElement = document.createElement('button');
        buttonElement.innerHTML = '<i class="fa fa-pencil" style="cursor: pointer !important;"></i>';
        buttonElement.id = 'ol-draw';
        buttonElement.addEventListener('click', this.drawingPolygon.bind(this));

        var divElement = document.createElement('div');
        divElement.className = 'ol-draw ol-unselectable ol-control';
        divElement.appendChild(buttonElement);

        this._OnStartPolygonDrawControl = new ol.control.Control({
            element: divElement
        });
        this.olmap.addControl(this._OnStartPolygonDrawControl);
    }

    drawingPolygon(e) {
        if (this.isDrawingEnabled) {
            console.log("you can't edit or draw features");
            return null;
        }
        var self = this;
        this.olmap.removeInteraction(this.draw);
        this.isDrawingEnabled = !this.isDrawingEnabled;
        var geometryFunction = null;
        if (this.isDrawingEnabled) {
            const editButton = this.mapContainerRef.el?.querySelector("#ol-draw");
            if (editButton) {
                editButton.innerHTML = "<i class='fa fa-play' style='cursor: pointer !important;'></i>";
            }
            this.isDrawingEnabled = false;

            this.draw = new ol.interaction.Draw({
                source: self.vectorSource,
                type: 'Polygon',
                geometryFunction: geometryFunction,
                name: 'draw',
            });

            this.olmap.addInteraction(this.draw);
            this.draw.on('drawend', this.drawingPolygonDrawEnd.bind(this));
            this.draw.on('drawstart', function (e) {
                self.vectorSource.clear();
            });

            this.modify = new ol.interaction.Modify({
                source: this.vectorSource,
                name: 'modify',
            });
            this.olmap.addInteraction(this.modify);
            this.modify.on('modifyend', this.drawingPolygonDrawEnd.bind(this));

            this.snap = new ol.interaction.Snap({
                source: this.vectorSource,
                name: 'snap',
            });
            this.olmap.addInteraction(this.snap);
        } else {
            const editButton = this.mapContainerRef.el?.querySelector("#ol-draw");
            if (editButton) {
                editButton.innerHTML = "<i class='fa fa-pencil' style='cursor: pointer !important;'></i>";
            }
            if (this.key) {
                ol.Observable.unByKey(this.key);
            }
        }
    }

    drawingPolygonDrawEnd(e) {
        var self = this;
        if (!this.isDrawingEnabled){
            this.isDrawingEnabled = false;
            if (this.draw) {
                this.olmap.removeInteraction(this.draw);
            }
            if (this.snap) {
                this.olmap.removeInteraction(this.snap);
            }
            if (this.modify) {
                this.olmap.removeInteraction(this.modify);
            }
            const editButton = this.mapContainerRef.el?.querySelector("#ol-draw");
            if (editButton) {
                editButton.innerHTML = "<i class='fa fa-pencil' style='cursor: pointer !important;'></i>";
            }
            setTimeout(function () {
                self.fieldChanged();
            }, 100);
        }
    }

    addPolygonClearControl() {
        var buttonElement = document.createElement('button');
        buttonElement.innerHTML = '<i class="fa fa-trash" style="cursor: pointer !important; position: relative;"></i>';
        buttonElement.id = 'ol-clear';
        buttonElement.addEventListener('click', this.clearPolygon.bind(this));

        var divElement = document.createElement('div');
        divElement.className = 'ol-clear ol-unselectable ol-control';
        divElement.appendChild(buttonElement);

        this._OnDeletePolygonDrawControl = new ol.control.Control({
            element: divElement
        });
        this.olmap.addControl(this._OnDeletePolygonDrawControl);
    }

    clearPolygon() {
        var self = this;
        this.isDrawingEnabled = false;
        if (this.draw) {
            this.olmap.removeInteraction(this.draw);
        }
        if (this.snap) {
            this.olmap.removeInteraction(this.snap);
        }
        if (this.modify) {
            this.olmap.removeInteraction(this.modify);
        }
        self.vectorSource.clear();
        self.circleFeature = null;
        // Clear input fields
        const clearValues = {};
        if (this.props.record.data.input_latitude !== undefined) {
            clearValues.input_latitude = 0;
        }
        if (this.props.record.data.input_longitude !== undefined) {
            clearValues.input_longitude = 0;
        }
        if (this.props.record.data.input_radius !== undefined) {
            clearValues.input_radius = 0;
        }
        if (Object.keys(clearValues).length > 0) {
            this.props.record.update(clearValues);
        }
        self.fieldChanged();
    }
    
    drawCircleFromInputs() {
        const self = this;
        const lat = this.props.record.data.input_latitude;
        const lon = this.props.record.data.input_longitude;
        const radius = this.props.record.data.input_radius;
        
        // Check if we have all required values
        if (!lat || !lon || !radius || radius <= 0) {
            return;
        }
        
        // Validate coordinates
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            console.warn('Invalid coordinates:', { lat, lon });
            return;
        }
        
        // Remove existing circle feature if any
        if (self.circleFeature) {
            self.vectorSource.removeFeature(self.circleFeature);
            self.circleFeature = null;
        }
        
        // Clear any other features
        self.vectorSource.clear();
        
        // Create a circle geometry
        // OpenLayers Circle uses meters in the projected coordinate system (EPSG:3857)
        // The center needs to be in projected coordinates
        const center = ol.proj.fromLonLat([lon, lat]);
        
        // Create circle with radius in meters (OpenLayers handles the conversion)
        const circle = new ol.geom.Circle(center, radius);
        
        // Convert circle to polygon (approximate with 64 points for smooth circle)
        const polygon = ol.geom.Polygon.fromCircle(circle, 64);
        
        // Create feature from polygon
        const feature = new ol.Feature({
            geometry: polygon,
            name: 'Geofence Circle'
        });
        
        // Style the feature
        feature.setStyle(new ol.style.Style({
            fill: new ol.style.Fill({
                color: 'rgb(255 235 59 / 62%)',
            }),
            stroke: new ol.style.Stroke({
                color: '#ffc107',
                width: 2,
            }),
        }));
        
        // Add to map
        self.vectorSource.addFeature(feature);
        self.circleFeature = feature;
        
        // Center and zoom map to show the circle (zoomed out one more level)
        const extent = polygon.getExtent();
        self.olmap.getView().fit(extent, {
            padding: [50, 50, 50, 50],
            maxZoom: 18
        });
        
        // Zoom out one more level
        const currentZoom = self.olmap.getView().getZoom();
        if (currentZoom !== undefined) {
            self.olmap.getView().setZoom(currentZoom - 1);
        }
        
        // Update the overlay_paths field
        setTimeout(() => {
            self.fieldChanged();
        }, 100);
    }
    
    watchInputFields() {
        const self = this;
        
        // Use a small delay to batch multiple field changes
        if (this.fieldWatchTimeout) {
            clearTimeout(this.fieldWatchTimeout);
        }
        
        this.fieldWatchTimeout = setTimeout(() => {
            self.drawCircleFromInputs();
        }, 500);
    }

    async fieldChanged() {
        console.log('=== FIELD CHANGED TRACE START ===');
        var getFeatures = this.vectorSource.getFeatures();
        console.log('Features from vector source:', getFeatures);
        var _newValue = new ol.format.GeoJSON().writeFeatures(getFeatures);
        console.log('GeoJSON value:', _newValue);
        
        // Calculate all computed fields
        let computedValues = {
            [this.props.name]: _newValue || 'Empty'
        };
        console.log('Initial computed values:', computedValues);
        
        if (_newValue && _newValue !== 'Empty') {
            console.log('Processing non-empty geofence data...');
            try {
                const geojson = JSON.parse(_newValue);
                console.log('Parsed GeoJSON:', geojson);
                let geometry = geojson;
                
                // Handle both Feature and Geometry objects
                if (geojson.type === 'Feature') {
                    geometry = geojson.geometry;
                    console.log('Using geometry from Feature:', geometry);
                }
                
                if (geometry && geometry.type === 'Polygon' && geometry.coordinates && geometry.coordinates[0]) {
                    const coordinates = geometry.coordinates[0];
                    console.log('Polygon coordinates found:', coordinates.length, 'points');
                    
                    // Check if coordinates are in projected system (large numbers) or GPS (small numbers)
                    const firstCoord = coordinates[0];
                    const isProjected = Math.abs(firstCoord[0]) > 1000 || Math.abs(firstCoord[1]) > 1000;
                    
                    let gpsCoordinates = coordinates;
                    
                    if (isProjected) {
                        console.log('Converting projected coordinates to GPS...');
                        // Convert projected coordinates to GPS using OpenLayers
                        gpsCoordinates = coordinates.map(coord => {
                            const gpsCoord = ol.proj.toLonLat([coord[0], coord[1]]);
                            return [gpsCoord[0], gpsCoord[1]];
                        });
                        console.log('Converted coordinates:', gpsCoordinates.slice(0, 3));
                    }
                    
                    // Calculate center point
                    let xSum = 0, ySum = 0;
                    for (const coord of gpsCoordinates) {
                        xSum += coord[0];
                        ySum += coord[1];
                    }
                    const centerX = xSum / gpsCoordinates.length;
                    const centerY = ySum / gpsCoordinates.length;
                    
                    // Calculate approximate radius (in degrees, then convert to meters)
                    let maxDistance = 0;
                    for (const coord of gpsCoordinates) {
                        const distance = Math.sqrt(Math.pow(coord[0] - centerX, 2) + Math.pow(coord[1] - centerY, 2));
                        maxDistance = Math.max(maxDistance, distance);
                    }
                    const radius = maxDistance * 111320; // Rough conversion to meters
                    
                    // Calculate area using shoelace formula (in square degrees, then convert to square meters)
                    let area = 0;
                    const n = gpsCoordinates.length;
                    for (let i = 0; i < n; i++) {
                        const j = (i + 1) % n;
                        area += gpsCoordinates[i][0] * gpsCoordinates[j][1];
                        area -= gpsCoordinates[j][0] * gpsCoordinates[i][1];
                    }
                    const areaSize = Math.abs(area) * 12392; // Rough conversion to square meters
                    
                    // Update all computed fields
                    computedValues.center_latitude = centerY;
                    computedValues.center_longitude = centerX;
                    computedValues.radius = radius;
                    computedValues.coordinates_count = gpsCoordinates.length;
                    computedValues.area_size = areaSize;
                    computedValues.is_valid = gpsCoordinates.length >= 3;
                    
                    console.log('Calculated values:', {
                        center_latitude: centerY,
                        center_longitude: centerX,
                        radius: radius,
                        coordinates_count: gpsCoordinates.length,
                        area_size: areaSize,
                        is_valid: gpsCoordinates.length >= 3,
                        isProjected: isProjected
                    });
                } else {
                    // Reset values for invalid geometry
                    computedValues.center_latitude = 0;
                    computedValues.center_longitude = 0;
                    computedValues.radius = 0;
                    computedValues.coordinates_count = 0;
                    computedValues.area_size = 0;
                    computedValues.is_valid = false;
                }
            } catch (error) {
                console.error('Error parsing geojson:', error);
                // Reset values on error
                computedValues.center_latitude = 0;
                computedValues.center_longitude = 0;
                computedValues.radius = 0;
                computedValues.coordinates_count = 0;
                computedValues.area_size = 0;
                computedValues.is_valid = false;
            }
        } else {
            // Reset values for empty geofence
            computedValues.center_latitude = 0;
            computedValues.center_longitude = 0;
            computedValues.radius = 0;
            computedValues.coordinates_count = 0;
            computedValues.area_size = 0;
            computedValues.is_valid = false;
        }
        
        // Update all fields at once
        console.log('=== FINAL UPDATE SECTION ===');
        console.log('Record ID:', this.props.record.resId);
        console.log('Updating geofence with values:', computedValues);
        
        try {
            await this.props.record.update(computedValues);
            console.log('Record update completed');
            
            // Force a database write to ensure persistence
            await this.orm.write('hr.attendance.geofence', [this.props.record.resId], computedValues);
            console.log('Database write completed');
            
            // Reload the record to refresh the UI
            await this.props.record.load();
            console.log('Record reloaded');
            
            // Check if fields were actually updated
            console.log('=== FIELD VALUES AFTER UPDATE ===');
            console.log('center_latitude:', this.props.record.data.center_latitude);
            console.log('center_longitude:', this.props.record.data.center_longitude);
            console.log('radius:', this.props.record.data.radius);
            console.log('coordinates_count:', this.props.record.data.coordinates_count);
            console.log('area_size:', this.props.record.data.area_size);
            console.log('is_valid:', this.props.record.data.is_valid);
            
        } catch (error) {
            console.error('Error in update process:', error);
        }
        
        console.log('=== FIELD CHANGED TRACE END ===');
    }
}

export const GeofenceDrawingField = {
    component: GeofenceDrawing,
    displayName: _t("Geofence Drawing"),
    supportedTypes: ["text"],
};

registry.category("fields").add("geofence_drawing", GeofenceDrawingField);
