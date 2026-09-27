/** @odoo-module */

import PublicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

export const timeOffPortal = PublicWidget.Widget.extend({
    selector: '#wrapwrap:has(.create_new_timeoff_form, .edit_timeoff_form)',
    events: {
        'change select.holiday_status_id' : function (e) {
            e.preventDefault();
            var self = this;
            self.$("#request_unit_half").prop("checked", false);
            self.$("#request_unit_hours").prop("checked", false);
            self.$('.request_hour_div').hide();
            self.$('.request_date_from_period_div').hide();
            self._onChangeHolidayStatus(this.$('select.holiday_status_id').val());
            self.$('#request_date_to_div').show();
        },
        'change input.request_unit_half' : function(e){
            e.preventDefault();
            var self = this;
            self.$("#request_unit_hours").prop("checked", false);
            self.$('.request_hour_div').hide();
            self.$('.select_request_hour').removeAttr('required');
            self.$('.select_request_hour').val('');
            self.check_request_date_from_period(this.$('input.request_unit_half'));
        },
        'change input.request_unit_hours' : function(e){
            e.preventDefault();
            var self = this;
            self.$("#request_unit_half").prop("checked", false);
            self.$('#request_date_from_period_div').hide();
            self.$('#request_date_from_period').removeAttr('required');
            self.$('#request_date_from_period').val('');
            self.check_request_custom_hours(this.$('input.request_unit_hours'));
        },
        'click .create_new_timeoff_form .create_new_timeoff_confirm': '_onCreateNewTimeoffRequest',
        'click .edit_timeoff_form .edit_timeoff_confirm': '_onEditTimeOffRequest',
        'click .o_delete_action_button' : '_onDeleteTimeoffRequest',
    },
    _buttonExec: function ($btn, callback) {
        $btn.prop('disabled', true);
        return callback.call(this).catch(function (e) {
            $btn.prop('disabled', false);
            // Log error but don't reject - let the callback handle errors
            console.error("Error in button execution:", e);
        });
    },

    init() {
        this._super(...arguments);
        this.notification = this.bindService("notification");
        this.dialog = this.bindService("dialog");
    },
    start: function () {
        var self = this;
        this._showPendingPortalWarning();
        return Promise.all([
            this._super(),
            this.$('.holiday_status_id').each(function () {
                self._onChangeHolidayStatus($(this).val());
            }),
            this.$('#request_unit_half').each(function(){
                self.check_request_date_from_period($(this));
            }),
            this.$('#request_unit_hours').each(function(){
                self.check_request_custom_hours($(this));
            }),
        ])
    },
    _getWarningStorageKey: function () {
        return 'pt_timeoff_portal_warning';
    },
    _storePortalWarning: function (warning) {
        if (!warning || !window.sessionStorage) {
            return;
        }
        window.sessionStorage.setItem(this._getWarningStorageKey(), JSON.stringify(warning));
    },
    _showPendingPortalWarning: function () {
        if (!window.sessionStorage) {
            return;
        }
        const key = this._getWarningStorageKey();
        const rawWarning = window.sessionStorage.getItem(key);
        if (!rawWarning) {
            return;
        }
        window.sessionStorage.removeItem(key);
        try {
            this._showPortalWarning(JSON.parse(rawWarning));
        } catch (_error) {
            // Ignore malformed cached warnings.
        }
    },
    _showPortalWarning: function (warning) {
        if (!warning) {
            return;
        }
        const message = warning.title
            ? `${warning.title}: ${warning.message}`
            : warning.message;
        this.notification.add(
            message,
            { type: 'warning', sticky: true }
        );
    },
    _onChangeHolidayStatus: async function(val){
        var self = this;
        await rpc("/web/dataset/call_kw/hr.leave.type/search_read", {
            model: "hr.leave.type",
            method: "search_read",
            args: [[['id', '=', val]], ['id', 'request_unit']],
            kwargs: {},
        }).then(function(rec){
            if (rec && rec[0]){
                if (rec[0].request_unit == 'hour'){
                    $('.request_unit_half_div').show();
                    $('.request_unit_hours_div').show();
                }
                else if (rec[0].request_unit == 'half_day'){
                    $('.request_unit_half_div').show();
                    $('.request_unit_hours_div').hide();                     
                }
                else{
                    $('.request_unit_half_div').hide();
                    $('.request_unit_hours_div').hide();
                    $('.request_date_from_div').show();
                }
            }
        });          
    },
    check_request_date_from_period: function($this){
        var self = this;
        var $request_date_from_period_div = $('#request_date_from_period_div');
        var $request_date_to_div = $('#request_date_to_div');
        var $request_date_from_period = $request_date_from_period_div.find('#request_date_from_period');
        if ($this.prop('checked'))
        {
            $request_date_from_period_div.show();                
            $request_date_from_period.attr('required','required');
            setTimeout(function() {
                $request_date_to_div.hide();
                $request_date_to_div.find('.request_date_to').val('');
            }, 10);               
        }
        else
        {   
            $request_date_from_period_div.hide();
            $request_date_from_period.removeAttr('required');
            $request_date_from_period.val('');
            $request_date_to_div.show();
        }
    },
    check_request_custom_hours: function($this){
        var $request_hour_div = $('.request_hour_div');
        var $request_date_to_div = $('#request_date_to_div');
        var $select_request_hour = $request_hour_div.find('.select_request_hour');
        if ($this.prop('checked'))
        {
            $request_hour_div.show();
            $select_request_hour.attr('required','required');
            setTimeout(function() {
                $request_date_to_div.hide();
                $request_date_to_div.find('.request_date_to').val('');
            }, 10);
        }
        else
        {
            $request_hour_div.hide();
            $select_request_hour.removeAttr('required');
            $select_request_hour.val('');
            $request_date_to_div.show();
        }
    },
    _onCreateNewTimeoffRequest: function(ev){
        ev.preventDefault();
        ev.stopPropagation();
        
        var name = $('.create_new_timeoff_form .name').val();
        var request_date_from = $('.create_new_timeoff_form .request_date_from').val();
        var request_date_to = $('.create_new_timeoff_form .request_date_to').val();
        var request_unit_half = $('.create_new_timeoff_form .request_unit_half').prop("checked");
        var request_date_from_period = $('.create_new_timeoff_form .request_date_from_period').val();
        var request_unit_hours = $('.create_new_timeoff_form .request_unit_hours').prop("checked");
        var request_hour_from = $('.create_new_timeoff_form .request_hour_from').val();
        var request_hour_to = $('.create_new_timeoff_form .request_hour_to').val();
        
        if (!name) {
            this.notification.add(
                _t("Please Enter Description."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        
        if (!request_date_from) {
            this.notification.add(
                _t("Please Enter From Date."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        
        if (request_unit_half && !request_date_from_period) {
            this.notification.add(
                _t("Please Enter From Period."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        
        if (request_unit_hours && (!request_hour_from || !request_hour_to)) {
            this.notification.add(
                _t("Please Enter From and To Hours."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        
        if (!request_unit_half && !request_unit_hours && !request_date_to) {
            this.notification.add(
                _t("Please Enter To Date."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        
        if (request_date_from && request_date_to && !request_unit_half && !request_unit_hours) {
            var from = this._parseDate(request_date_from);
            var to = this._parseDate(request_date_to);
            
            if (to < from) {
                this.notification.add(
                    _t("To Date cannot be earlier than From Date."),
                    { type: 'danger', sticky: true }
                );
                return;
            }
        }

        this._buttonExec($(ev.currentTarget), this._createNewTimeOff);
    },
    
    _parseDate: function (dateStr) {
        if (!dateStr) {
            return false;
        }

        const value = String(dateStr).trim();

        const arabicMonths = {
            // January
            'يناير': 0,
            'جانفي': 0,
            // February
            'فبراير': 1,
            'فيفري': 1,
            // March
            'مارس': 2,
            // April
            'أبريل': 3,
            'ابريل': 3,
            // May
            'مايو': 4,
            'ماي': 4,
            // June
            'يونيو': 5,
            'جوان': 5,
            // July
            'يوليو': 6,
            'يوليوز': 6,
            // August
            'أغسطس': 7,
            'اغسطس': 7,
            // September
            'سبتمبر': 8,
            // October
            'أكتوبر': 9,
            'اكتوبر': 9,
            // November
            'نوفمبر': 10,
            // December
            'ديسمبر': 11,
        };

        const englishMonths = {
            'january': 0, 'jan': 0,
            'february': 1, 'feb': 1,
            'march': 2, 'mar': 2,
            'april': 3, 'apr': 3,
            'may': 4,
            'june': 5, 'jun': 5,
            'july': 6, 'jul': 6,
            'august': 7, 'aug': 7,
            'september': 8, 'sep': 8, 'sept': 8,
            'october': 9, 'oct': 9,
            'november': 10, 'nov': 10,
            'december': 11, 'dec': 11,
        };

        // YYYY-MM-DD
        if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
            const [year, month, day] = value.split('-').map(Number);
            const d = new Date(year, month - 1, day);
            return isNaN(d.getTime()) ? false : d;
        }

        // DD/MM/YYYY or MM/DD/YYYY
        if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(value)) {
            const [a, b, year] = value.split('/').map(Number);
            let day, month;
            if (a > 12) {
                day = a; month = b;
            } else if (b > 12) {
                month = a; day = b;
            } else {
                month = a; day = b;
            }
            const d = new Date(year, month - 1, day);
            return isNaN(d.getTime()) ? false : d;
        }

        // Normalize: remove commas, normalize spaces
        const cleaned = value.replace(/،/g, ' ').replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
        const parts = cleaned.split(' ');

        const allMonths = { ...arabicMonths, ...englishMonths };

        const isMonth = (str) => allMonths.hasOwnProperty(str) || allMonths.hasOwnProperty(str.toLowerCase());
        const getMonth = (str) => allMonths[str] !== undefined ? allMonths[str] : allMonths[str.toLowerCase()];

        if (parts.length === 3) {
            const [p0, p1, p2] = parts;

            // "07 أبريل 2026" or "07 April 2026"
            if (/^\d{1,2}$/.test(p0) && isMonth(p1) && /^\d{4}$/.test(p2)) {
                const d = new Date(Number(p2), getMonth(p1), Number(p0));
                return isNaN(d.getTime()) ? false : d;
            }

            // "أبريل 07 2026" or "April 07 2026"
            if (isMonth(p0) && /^\d{1,2}$/.test(p1) && /^\d{4}$/.test(p2)) {
                const d = new Date(Number(p2), getMonth(p0), Number(p1));
                return isNaN(d.getTime()) ? false : d;
            }

            // "أبريل 2026 07" or "April 2026 07"
            if (isMonth(p0) && /^\d{4}$/.test(p1) && /^\d{1,2}$/.test(p2)) {
                const d = new Date(Number(p1), getMonth(p0), Number(p2));
                return isNaN(d.getTime()) ? false : d;
            }

            // "2026 أبريل 07" or "2026 April 07"
            if (/^\d{4}$/.test(p0) && isMonth(p1) && /^\d{1,2}$/.test(p2)) {
                const d = new Date(Number(p0), getMonth(p1), Number(p2));
                return isNaN(d.getTime()) ? false : d;
            }

            // "2026 07 أبريل" or "2026 07 April"
            if (/^\d{4}$/.test(p0) && /^\d{1,2}$/.test(p1) && isMonth(p2)) {
                const d = new Date(Number(p0), getMonth(p2), Number(p1));
                return isNaN(d.getTime()) ? false : d;
            }
        }

        // Fallback: try native Date parsing
        const native = new Date(value);
        return isNaN(native.getTime()) ? false : native;
    },
    _createNewTimeOff: async function() {
        var self = this;
        return await rpc("/web/dataset/call_kw/hr.leave/create_timeoff_portal", {
            model: "hr.leave",
            method: "create_timeoff_portal",
            args: [{
                name: $('.create_new_timeoff_form .name').val(),
                holiday_status_id: $('.create_new_timeoff_form .holiday_status_id').val(),
                request_date_from: this._parse_date($('.create_new_timeoff_form .request_date_from').val()),
                request_date_to: this._parse_date($('.create_new_timeoff_form .request_date_to').val()),
                request_unit_half: $('.create_new_timeoff_form .request_unit_half').prop("checked"),
                request_date_from_period: $('.create_new_timeoff_form .request_date_from_period').val(),
                request_unit_hours: $('.create_new_timeoff_form .request_unit_hours').prop("checked"),
                request_hour_from: $('.create_new_timeoff_form .request_hour_from').val(),
                request_hour_to: $('.create_new_timeoff_form .request_hour_to').val(),                    
            }],
            kwargs: {},
        }).then(function (response) {
            if (response && response.warning) {
                self._storePortalWarning(response.warning);
            }
            if (response && response.errors) {
                $('#new-timeoff-dialog .alert').remove();
                const formattedError = response.errors.replace(/\n/g, "<br/>");
                const $firstRow = $('#new-timeoff-dialog .row.mt16').first();
                $firstRow.before('<div class="alert alert-danger">' + formattedError + '</div>');
            } 
            else if (response && response.id) {
                window.location = '/my/leave/' + response.id + '?access_token=' + response.access_token;
            }
            $('.create_new_timeoff_confirm').prop('disabled', '');
        });
    },
    _onEditTimeOffRequest: function(ev){
        ev.preventDefault();
        ev.stopPropagation();
        var name = $('.edit_timeoff_form .name').val();
        if (!name) {
            this.notification.add(
                _t("Please Enter Description."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        var request_date_from = $('.edit_timeoff_form .request_date_from').val();
        if (!request_date_from) {
            this.notification.add(
                _t("Please Enter From Date."),
                { type: 'danger', sticky: true }
            );
            return;
        }            
        
        var request_unit_half = $('.edit_timeoff_form .request_unit_half').prop("checked");
        var request_date_from_period = $('.edit_timeoff_form .request_date_from_period').val();
        if (request_unit_half && !request_date_from_period) {
            this.notification.add(
                _t("Please Enter From Period."),
                { type: 'danger', sticky: true }
            );
            return;
        }

        var request_unit_hours = $('.edit_timeoff_form .request_unit_hours').prop("checked");
        var request_hour_from = $('.edit_timeoff_form .request_hour_from').val();
        var request_hour_to =$('.edit_timeoff_form .request_hour_to').val();

        if (request_unit_hours && (!request_hour_from || !request_hour_to)) {
            this.notification.add(
                _t("Please Enter From Period."),
                { type: 'danger', sticky: true }
            );
            return;
        }

        var request_date_to = $('.edit_timeoff_form .request_date_to').val();
        if (!request_date_to && !request_unit_half && !request_unit_hours) {
            this.notification.add(
                _t("Please Enter To Period."),
                { type: 'danger', sticky: true }
            );
            return;
        }
        this._buttonExec($(ev.currentTarget), this._onEditTimeOff);
    },
    _onEditTimeOff: async function(){
        var self = this;
        return await rpc("/web/dataset/call_kw/hr.leave/update_timeoff_portal", {
            model: "hr.leave",
            method: "update_timeoff_portal",
            args: [{
                leave_id: parseInt($('.edit_timeoff_form .leave_id').val()),

                name: $('.edit_timeoff_form .name').val(),
                holiday_status_id: $('.edit_timeoff_form .holiday_status_id').val(),

                request_date_from: this._parse_date($('.edit_timeoff_form .request_date_from').val()),
                request_date_to: this._parse_date($('.edit_timeoff_form .request_date_to').val()),
                
                request_unit_half: $('.edit_timeoff_form .request_unit_half').prop("checked"),
                request_date_from_period: $('.edit_timeoff_form .request_date_from_period').val(),

                request_unit_hours: $('.edit_timeoff_form .request_unit_hours').prop("checked"),
                request_hour_from: $('.edit_timeoff_form .request_hour_from').val(),
                request_hour_to: $('.edit_timeoff_form .request_hour_to').val(),       
            }],
            kwargs: {},
        }).then(function (response) {
            if (response && response.warning) {
                self._storePortalWarning(response.warning);
            }
            if (response && response.errors) {
                $('#new-timeoff-dialog .alert').remove();
                const formattedError = response.errors.replace(/\n/g, "<br/>");
                const $firstRow = $('#new-timeoff-dialog .row.mt16').first();
                $firstRow.before('<div class="alert alert-danger">' + formattedError + '</div>');
            } 
            else if (response && response.id) {
                window.location.reload();
            }
            $('.edit_timeoff_confirm').prop('disabled', '');              
        });
    },
    _onDeleteTimeoffRequest: function(ev){
        var self = this;
        ev.preventDefault();
        ev.stopPropagation();
        var leave_id = parseInt(ev.currentTarget.value);
        if(leave_id){
            if (confirm(_t("This will delete the Time Off. Do you still want to proceed ?"))) {
                self._onDeleteTimeOff(leave_id);
            }
        }            
    },
    _onDeleteTimeOff: async function (leave_id) {  
        var self = this;     
        await rpc("/web/dataset/call_kw/hr.leave/unlink_portal", {
            model: "hr.leave",
            method: "unlink_portal",
            args: [{
                leave_id :  leave_id
            }], 
            kwargs: {},
        }).then(function(result){
            if (result === true || (result && result.success)) {
                window.location = '/my/leaves/';
            }else{
                self.notification.add(
                    (result && result.error) || _t("Something went wrong during your Time off deletion."),
                    { type: 'danger', sticky: true }
                );
            }
        });
    },
    _parse_date: function (value) {
        const parsed = this._parseDate(value);
        if (!parsed) {
            return false;
        }

        const year = parsed.getFullYear();
        const month = String(parsed.getMonth() + 1).padStart(2, '0');
        const day = String(parsed.getDate()).padStart(2, '0');

        return `${year}-${month}-${day} 00:00:00`;
    },
});
PublicWidget.registry.timeOffPortal = timeOffPortal;

// Workaround for zoomOdoo error on portal pages
// This prevents the website_root widget from failing when zoomOdoo plugin is not available
if (typeof jQuery !== 'undefined' && !jQuery.fn.zoomOdoo) {
    jQuery.fn.zoomOdoo = function() {
        // No-op function to prevent errors
        return this;
    };
}
