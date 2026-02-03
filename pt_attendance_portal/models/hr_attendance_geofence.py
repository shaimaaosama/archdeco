from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.tools import safe_eval

class HrAttendanceGeofence(models.Model):
    """Model for defining virtual geographic boundaries for attendance locations"""
    _name = "hr.attendance.geofence"
    _description = "Attendance Geofence"
    _order = "id desc"
    
    # Basic geofence information
    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s: s.env.company.id, index=True)
    
    # Employee assignments to this geofence
    employee_ids = fields.Many2many('hr.employee', 'employee_geofence_rel', 'geofence_id', 'emp_id', string='Employees')
    
    # Geographic boundary data (JSON format for polygon coordinates)
    overlay_paths = fields.Text(string='Paths')
    
    # Additional fields for better geofence management
    center_latitude = fields.Float('Center Latitude', digits=(16, 8), help='Center latitude of the geofence')
    center_longitude = fields.Float('Center Longitude', digits=(16, 8), help='Center longitude of the geofence')
    radius = fields.Float('Radius (meters)', help='Approximate radius of the geofence in meters')
    
    # Input fields for manual coordinate entry
    input_latitude = fields.Float('Latitude', digits=(16, 8), help='Enter latitude to create geofence circle')
    input_longitude = fields.Float('Longitude', digits=(16, 8), help='Enter longitude to create geofence circle')
    input_radius = fields.Float('Allowed Distance (meters)', help='Enter radius in meters to create geofence circle')
    
    # Regular fields for better display (updated directly from JavaScript)
    coordinates_count = fields.Integer('Coordinates Count', help='Number of coordinate points')
    area_size = fields.Float('Area Size (sq meters)', help='Area size in square meters')
    
    # Status and validation
    active = fields.Boolean('Active', default=True)
    is_valid = fields.Boolean('Valid Geofence', help='Indicates if the geofence has valid coordinates')
    
    
    @api.model
    def update_geofence_with_computed_fields(self, geofence_id, overlay_paths):
        """Update geofence with overlay_paths and compute all related fields"""
        geofence = self.browse(geofence_id)
        if not geofence.exists():
            return False
            
        # Calculate computed values
        computed_values = {
            'overlay_paths': overlay_paths,
            'center_latitude': 0.0,
            'center_longitude': 0.0,
            'radius': 0.0,
            'coordinates_count': 0,
            'area_size': 0.0,
            'is_valid': False
        }
        
        if overlay_paths and overlay_paths.strip() and overlay_paths != 'Empty':
            try:
                import json
                geojson = json.loads(overlay_paths)
                
                # Handle both Feature and Geometry objects
                if geojson.get('type') == 'Feature':
                    geometry = geojson.get('geometry', {})
                else:
                    geometry = geojson
                
                if geometry and geometry.get('type') == 'Polygon':
                    coordinates = geometry.get('coordinates', [])
                    if coordinates and len(coordinates) > 0:
                        outer_ring = coordinates[0]
                        
                        # Calculate center point
                        center = geofence._calculate_polygon_center(outer_ring)
                        computed_values['center_latitude'] = center[1]
                        computed_values['center_longitude'] = center[0]
                        
                        # Calculate approximate radius
                        computed_values['radius'] = geofence._calculate_polygon_radius(outer_ring, center)
                        
                        # Calculate area
                        computed_values['area_size'] = geofence._calculate_polygon_area(outer_ring)
                        
                        # Set other values
                        computed_values['coordinates_count'] = len(outer_ring)
                        computed_values['is_valid'] = len(outer_ring) >= 3
                        
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error parsing overlay_paths: {e}")
        
        # Write all values at once
        geofence.write(computed_values)
        return True
    
    
    def is_point_inside_geofence(self, latitude, longitude):
        """Check if a point is inside the geofence polygon"""
        if not self.overlay_paths or self.overlay_paths == 'Empty':
            return False
        
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            import json
            geojson = json.loads(self.overlay_paths)
            
            _logger.info(f"Checking point ({latitude}, {longitude}) against geofence {self.name}")
            _logger.info(f"Raw geojson type: {geojson.get('type', 'unknown')}")
            
            # Handle both Feature and Geometry objects
            if geojson.get('type') == 'Feature':
                geometry = geojson.get('geometry', {})
            else:
                geometry = geojson
            
            if not geometry or geometry.get('type') != 'Polygon':
                _logger.error(f"Invalid geometry type: {geometry.get('type') if geometry else 'None'}")
                return False
            
            coordinates = geometry.get('coordinates', [])
            if not coordinates or not coordinates[0]:
                _logger.error("No coordinates found in polygon")
                return False
            
            # Get the outer ring of the polygon
            polygon = coordinates[0]
            _logger.info(f"Polygon has {len(polygon)} points")
            
            # Use ray casting algorithm with GPS coordinates
            return self._point_in_polygon_gps(latitude, longitude, polygon)
            
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error in geofence {self.name}: {e}")
            return False
        except Exception as e:
            _logger.error(f"Error checking point in geofence {self.name}: {e}")
            return False
    
    def _point_in_polygon_gps(self, lat, lon, polygon):
        """Ray casting algorithm specifically for GPS coordinates"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Check if polygon coordinates are in GPS format
            if len(polygon) == 0:
                return False
                
            # Ensure we're working with GPS coordinates
            valid_gps_coords = True
            for coord in polygon[:5]:  # Check first 5 points
                if len(coord) >= 2:
                    x, y = coord[0], coord[1]
                    # GPS coordinates should be: longitude [-180,180], latitude [-90,90]
                    if abs(x) > 180 or abs(y) > 90:
                        valid_gps_coords = False
                        break
            
            if not valid_gps_coords:
                _logger.error("Polygon coordinates are not in GPS format")
                _logger.error("Cannot perform point-in-polygon check with mismatched coordinate systems")
                return False
            
            # Standard ray casting algorithm
            x, y = lon, lat  # Convert to x,y for algorithm
            n = len(polygon)
            inside = False
            
            p1x, p1y = polygon[0][0], polygon[0][1]
            for i in range(1, n + 1):
                p2x, p2y = polygon[i % n][0], polygon[i % n][1]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y
            
            _logger.info(f"Point ({lat}, {lon}) is {'inside' if inside else 'outside'} polygon")
            return inside
            
        except Exception as e:
            _logger.error(f"Error in GPS point-in-polygon calculation: {e}")
            return False
    
    @api.model
    def get_geofences_for_employee(self, employee_id, company_id=None):
        """Get active geofences for a specific employee"""
        domain = [
            ('active', '=', True),
            ('is_valid', '=', True),
            ('employee_ids', 'in', [employee_id])
        ]
        if company_id:
            domain.append(('company_id', '=', company_id))
        
        return self.search_read(domain, ['id', 'name', 'overlay_paths', 'center_latitude', 'center_longitude'])
    
    def check_employee_location(self, employee_id, latitude, longitude):
        """Check if employee location is within any of their assigned geofences"""
        geofences = self.search([
            ('active', '=', True),
            ('is_valid', '=', True),
            ('employee_ids', 'in', [employee_id]),
            ('company_id', '=', self.env.company.id)
        ])
        
        valid_geofences = []
        for geofence in geofences:
            if geofence.is_point_inside_geofence(latitude, longitude):
                valid_geofences.append(geofence)
        
        return valid_geofences
    
    def _calculate_polygon_area(self, coordinates):
        """Calculate approximate area of polygon using shoelace formula"""
        if not coordinates or len(coordinates) < 3:
            return 0.0
        
        area = 0.0
        n = len(coordinates)
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        
        # Convert to approximate square meters (very rough approximation)
        return abs(area) * 12392.0
    
    def _calculate_polygon_center(self, coordinates):
        """Calculate center point of polygon"""
        if not coordinates or len(coordinates) == 0:
            return [0.0, 0.0]
        
        x_sum = sum(coord[0] for coord in coordinates)
        y_sum = sum(coord[1] for coord in coordinates)
        count = len(coordinates)
        
        return [x_sum / count, y_sum / count]
    
    def _calculate_polygon_radius(self, coordinates, center):
        """Calculate approximate radius of polygon from center"""
        if not coordinates or not center:
            return 0.0
        
        max_distance = 0.0
        center_x, center_y = center
        
        for coord in coordinates:
            # Calculate distance from center to each point
            distance = ((coord[0] - center_x) ** 2 + (coord[1] - center_y) ** 2) ** 0.5
            max_distance = max(max_distance, distance)
        
        # Convert to approximate meters (very rough approximation)
        return max_distance * 111320.0