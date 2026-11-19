/** @odoo-module **/
import { Component, onWillStart, useState, useExternalListener } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AttendanceDashboard extends Component {
    static template = "hr_customs.AttendanceDashboard";
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        const today = new Date();
        this.viewOptions = [
            { value: "overview", label: "Attendance Overview", icon: "fa-dashboard" },
            { value: "department", label: "Department Overview", icon: "fa-building-o" },
            { value: "employee", label: "Employee Summary", icon: "fa-users" },
            { value: "daily", label: "Daily Attendance", icon: "fa-calendar-check-o" },
        ];
        this.sourceOptions = [{ value: "attendance", label: "Attendances" }, { value: "calendar", label: "Working Schedule" }, { value: "all", label: "All Sources" }];
        this.statusOptions = [
            { value: "all", label: "All Statuses" }, { value: "present", label: "Present" },
            { value: "late", label: "Late In" }, { value: "early", label: "Early Out" },
            { value: "late_early", label: "Late In or Early Out" }, { value: "absent", label: "Absent" },
            { value: "missing_in", label: "Missing Check-In" }, { value: "missing_out", label: "Missing Check-Out" },
            { value: "leave", label: "On Leave" }, { value: "weekend", label: "Weekend" },
            { value: "holiday", label: "Public Holiday" }, { value: "no_contract", label: "No Contract" },
        ];
        this.columns = [
            { key: "date", label: "Date" }, { key: "day", label: "Day" }, { key: "code", label: "Employee Code" },
            { key: "employee", label: "Employee" }, { key: "department", label: "Department" },
            { key: "shift", label: "Shift Name" }, { key: "shift_time", label: "Shift Start - End" },
            { key: "check_in", label: "Check In" }, { key: "check_out", label: "Check Out" },
            { key: "late", label: "Late In (Min)" }, { key: "early", label: "Early Out (Min)" },
            { key: "worked", label: "Worked Hours" }, { key: "overtime", label: "Overtime Hours" },
            { key: "status", label: "Status" }, { key: "remarks", label: "Remarks" },
        ];
        this.state = useState({
            loading: true, exporting: false, rows: [], employees: [], departments: [], summary: {},
            analytics: { employees: [], departments: [] }, viewMode: "overview", detailLevel: "",
            selectedDepartmentId: 0, selectedDepartmentName: "", selectedEmployeeId: 0, detailLoading: false,
            detail: { employee: {}, rows: [], date_from: "", date_to: "" }, total: 0, page: 1, limit: 100,
            dateFrom: "", dateTo: "", customDateFrom: "", customDateTo: "", customDateOpen: false,
            datePreset: "current_month", dateMode: "month", dateOpen: false,
            viewYear: today.getFullYear(), viewMonth: today.getMonth(), viewQuarter: Math.floor(today.getMonth() / 3),
            source: "attendance", status: "all", employeeIds: [], departmentIds: [],
            employeeSearch: "", departmentSearch: "", employeeOpen: false, departmentOpen: false,
            sourceOpen: false, statusOpen: false,
        });
        useExternalListener(window, "click", ev => {
            const target = ev.target instanceof Element ? ev.target : ev.target?.parentElement;
            if (!target?.closest(".aad-date-selector")) { this.state.dateOpen = false; this.state.customDateOpen = false; }
            if (!target?.closest(".aad-employee-filter")) this.state.employeeOpen = false;
            if (!target?.closest(".aad-department-filter")) this.state.departmentOpen = false;
            if (!target?.closest(".aad-source-filter")) this.state.sourceOpen = false;
            if (!target?.closest(".aad-status-filter")) this.state.statusOpen = false;
        });
        onWillStart(async () => {
            try {
                const options = await this.orm.call("attendance.analysis.dashboard", "get_filter_options", []);
                this.state.employees = options.employees || [];
                this.state.departments = options.departments || [];
                await this.loadData();
            } catch (error) {
                this.state.loading = false;
                this.notification.add("Unable to load Attendance Dashboard.", { type: "danger" });
                throw error;
            }
        });
    }
    get filters() {
        return { date_preset: this.state.datePreset, date_from: this.state.dateFrom, date_to: this.state.dateTo,
            source: this.state.source, status: this.state.status, employee_ids: [...this.state.employeeIds], department_ids: [...this.state.departmentIds] };
    }
    get cards() {
        const s = this.state.summary;
        return [
            { label: "TOTAL EMPLOYEES", value: s.employees || 0, icon: "fa-users", color: "orange" },
            { label: "PRESENT DAYS", value: s.present || 0, icon: "fa-check-circle", color: "green" },
            { label: "ABSENT DAYS", value: s.absent || 0, icon: "fa-user-times", color: "red" },
            { label: "ABSENCE RATE", value: `${s.absence_rate || 0}%`, icon: "fa-percent", color: "red" },
            { label: "LATE IN", value: s.late || 0, icon: "fa-clock-o", color: "amber" },
            { label: "EARLY OUT", value: s.early || 0, icon: "fa-sign-out", color: "amber" },
            { label: "LEAVE DAYS", value: s.leave || 0, icon: "fa-calendar-check-o", color: "purple" },
            { label: "MISSING CHECK-OUT", value: s.missing_out || 0, icon: "fa-exclamation-circle", color: "red" },
            { label: "SCHEDULED HOURS", value: this.hours(s.scheduled_hours), icon: "fa-calendar", color: "slate" },
            { label: "WORKED HOURS", value: this.hours(s.worked_hours), icon: "fa-hourglass-half", color: "blue" },
            { label: "OVERTIME HOURS", value: this.hours(s.overtime_hours), icon: "fa-clock-o", color: "blue" },
            { label: "ATTENDANCE RATE", value: `${s.attendance_rate || 0}%`, icon: "fa-line-chart", color: "green" },
        ];
    }
    get overviewMetrics() {
        const s = this.state.summary;
        return [
            { label: "Employees", value: s.employees || 0 }, { label: "Attendance Rate", value: `${s.attendance_rate || 0}%` },
            { label: "Present Days", value: s.present || 0 }, { label: "Absent Days", value: s.absent || 0 },
            { label: "Late In", value: s.late || 0 }, { label: "Early Out", value: s.early || 0 },
            { label: "Leave Days", value: s.leave || 0 }, { label: "Missing Check-Out", value: s.missing_out || 0 },
            { label: "Scheduled Hours", value: this.hours(s.scheduled_hours) }, { label: "Worked Hours", value: this.hours(s.worked_hours) },
            { label: "Hours Difference", value: this.hours(s.hours_difference) }, { label: "Overtime Hours", value: this.hours(s.overtime_hours) },
        ];
    }
    get filteredEmployees() {
        const search = this.state.employeeSearch.trim().toLowerCase();
        return this.state.employees.filter(employee => `${employee.name} ${employee.code}`.toLowerCase().includes(search));
    }
    get filteredDepartments() {
        const search = this.state.departmentSearch.trim().toLowerCase();
        return this.state.departments.filter(department => department.name.toLowerCase().includes(search));
    }
    get visibleEmployeeSummary() {
        const rows = this.state.analytics.employees || [];
        return this.state.viewMode === "department" && this.state.detailLevel ? rows.filter(row => row.department_id === this.state.selectedDepartmentId) : rows;
    }
    get selectedEmployeeLabel() { return this.state.employeeIds.length ? `${this.state.employeeIds.length} Employee(s) Selected` : "All Employees"; }
    get selectedDepartmentLabel() { return this.state.departmentIds.length ? `${this.state.departmentIds.length} Department(s) Selected` : "All Departments"; }
    get sourceLabel() { return this.sourceOptions.find(option => option.value === this.state.source)?.label || "Attendances"; }
    get statusLabel() { return this.statusOptions.find(option => option.value === this.state.status)?.label || "All Statuses"; }
    get monthName() { return new Date(this.state.viewYear, this.state.viewMonth, 1).toLocaleString("en-US", { month: "long" }); }
    get quarterLabel() {
        const first = new Date(this.state.viewYear, this.state.viewQuarter * 3, 1).toLocaleString("en-US", { month: "short" });
        const last = new Date(this.state.viewYear, this.state.viewQuarter * 3 + 2, 1).toLocaleString("en-US", { month: "short" });
        return `${first} - ${last} ${this.state.viewYear}`;
    }
    get dateLabel() {
        if (this.state.dateMode === "none") return "All Dates";
        if (this.state.dateMode === "month") return `${this.monthName} ${this.state.viewYear}`;
        if (this.state.dateMode === "quarter") return this.quarterLabel;
        if (this.state.dateMode === "year") return String(this.state.viewYear);
        return { today: "Today", yesterday: "Yesterday", this_week: "This Week", last_week: "Last Week", custom: "Custom Dates" }[this.state.dateMode] || "Select Dates";
    }
    get pageCount() { return Math.max(1, Math.ceil(this.state.total / this.state.limit)); }
    get firstRecord() { return this.state.total ? (this.state.page - 1) * this.state.limit + 1 : 0; }
    get lastRecord() { return Math.min(this.state.page * this.state.limit, this.state.total); }
    get pageTitle() {
        if (this.state.detailLevel === "employee_daily") return "Employee Daily Attendance";
        if (this.state.detailLevel === "department_employees") return `${this.state.selectedDepartmentName} - Employee Summary`;
        return this.viewOptions.find(option => option.value === this.state.viewMode)?.label || "Attendance Overview";
    }
    get exportLabel() {
        if (this.state.detailLevel === "employee_daily") return "Employee Daily Excel";
        if (this.state.detailLevel === "department_employees") return "Department Employees Excel";
        return { overview: "Overview Excel", department: "Department Excel", employee: "Employee Excel", daily: "Daily Excel" }[this.state.viewMode];
    }
    formatISO(date) { return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }
    formatDisplay(value) {
        if (!value) return "";
        const [year, month, day] = String(value).split("-");
        return day ? `${day}-${month}-${year}` : `${month}-${year}`;
    }
    hours(value) { return Number(value || 0).toFixed(2); }
    openDatePicker(ev) {
        const input = ev.currentTarget;
        if (typeof input.showPicker === "function") { try { input.showPicker(); } catch { input.focus(); } }
    }
    closeFilters() {
        for (const name of ["date", "employee", "department", "source", "status"]) this.state[`${name}Open`] = false;
        this.state.customDateOpen = false;
    }
    toggleFilter(name) {
        const key = `${name}Open`;
        const open = !this.state[key];
        this.closeFilters();
        this.state[key] = open;
    }
    selectView(view) {
        this.state.viewMode = view;
        this.state.detailLevel = "";
        this.state.selectedDepartmentId = 0;
        this.state.selectedDepartmentName = "";
        this.state.selectedEmployeeId = 0;
        this.closeFilters();
    }
    openDepartment(department) {
        this.state.viewMode = "department";
        this.state.selectedDepartmentId = department.id;
        this.state.selectedDepartmentName = department.name;
        this.state.selectedEmployeeId = 0;
        this.state.detailLevel = "department_employees";
        this.scrollToReport();
    }
    async openEmployee(employeeId) {
        const previousLevel = this.state.detailLevel;
        this.state.detailLoading = true;
        this.state.detailLevel = "employee_daily";
        this.state.selectedEmployeeId = employeeId;
        this.state.detail = { employee: {}, rows: [], date_from: "", date_to: "" };
        try {
            this.state.detail = await this.orm.call("attendance.analysis.dashboard", "get_employee_details", [this.filters, employeeId]);
            this.scrollToReport();
        } catch (error) {
            this.state.detailLevel = previousLevel;
            this.state.selectedEmployeeId = 0;
            this.notification.add("Unable to load employee attendance details.", { type: "danger" });
        } finally { this.state.detailLoading = false; }
    }
    handleRowKeydown(ev, type, record) {
        if (ev.key !== "Enter" && ev.key !== " ") return;
        ev.preventDefault();
        if (type === "department") this.openDepartment(record);
        else if (type === "employee") this.openEmployee(record);
    }
    backToReport() {
        if (this.state.detailLevel === "employee_daily" && this.state.viewMode === "department") this.state.detailLevel = "department_employees";
        else { this.state.detailLevel = ""; this.state.selectedDepartmentId = 0; this.state.selectedDepartmentName = ""; }
        this.state.selectedEmployeeId = 0;
        this.scrollToReport();
    }
    scrollToReport() { requestAnimationFrame(() => this.el?.querySelector(".aad-report-section")?.scrollIntoView({ behavior: "smooth", block: "start" })); }
    async setRange(start, end, mode) {
        this.state.dateFrom = this.formatISO(start);
        this.state.dateTo = this.formatISO(end);
        this.state.datePreset = "custom";
        this.state.dateMode = mode;
        this.closeFilters();
        await this.applyFilters();
    }
    async selectPeriod(mode) {
        const year = this.state.viewYear;
        let start, end;
        if (mode === "month") { start = new Date(year, this.state.viewMonth, 1); end = new Date(year, this.state.viewMonth + 1, 0); }
        else if (mode === "quarter") { const month = this.state.viewQuarter * 3; start = new Date(year, month, 1); end = new Date(year, month + 3, 0); }
        else { start = new Date(year, 0, 1); end = new Date(year, 11, 31); }
        await this.setRange(start, end, mode);
    }
    async shiftPeriod(mode, direction) {
        if (mode === "month") {
            const date = new Date(this.state.viewYear, this.state.viewMonth + direction, 1);
            this.state.viewYear = date.getFullYear(); this.state.viewMonth = date.getMonth(); this.state.viewQuarter = Math.floor(date.getMonth() / 3);
        } else if (mode === "quarter") {
            const date = new Date(this.state.viewYear, (this.state.viewQuarter + direction) * 3, 1);
            this.state.viewYear = date.getFullYear(); this.state.viewMonth = date.getMonth(); this.state.viewQuarter = Math.floor(date.getMonth() / 3);
        } else this.state.viewYear += direction;
        await this.selectPeriod(mode);
    }
    async selectQuickDate(mode) {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        let start = new Date(year, month, today.getDate());
        let end = new Date(start);
        if (mode === "yesterday") { start.setDate(start.getDate() - 1); end = new Date(start); }
        else if (mode === "this_week" || mode === "last_week") {
            const daysSinceSaturday = (today.getDay() + 1) % 7;
            start.setDate(start.getDate() - daysSinceSaturday - (mode === "last_week" ? 7 : 0));
            end = new Date(start); end.setDate(start.getDate() + 6);
        } else if (mode === "none") {
            this.state.dateMode = "none"; this.state.datePreset = "none"; this.state.dateFrom = ""; this.state.dateTo = "";
            this.closeFilters(); await this.applyFilters(); return;
        } else if (mode === "custom") {
            this.state.customDateFrom = this.state.dateFrom || this.formatISO(new Date(year, month, 1));
            this.state.customDateTo = this.state.dateTo || this.formatISO(today);
            this.state.customDateOpen = true; this.state.dateOpen = true; return;
        }
        await this.setRange(start, end, mode);
    }
    async applyCustomDates() {
        if (!this.state.customDateFrom || !this.state.customDateTo) { this.notification.add("Please select both start and end dates.", { type: "warning" }); return; }
        if (this.state.customDateFrom > this.state.customDateTo) { this.notification.add("The start date cannot be later than the end date.", { type: "warning" }); return; }
        this.state.dateFrom = this.state.customDateFrom;
        this.state.dateTo = this.state.customDateTo;
        this.state.datePreset = "custom"; this.state.dateMode = "custom";
        this.closeFilters(); await this.applyFilters();
    }
    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("attendance.analysis.dashboard", "get_dashboard_data", [this.filters, this.state.page, this.state.limit]);
            this.state.rows = data.rows || [];
            this.state.summary = data.summary || {};
            this.state.analytics = data.analytics || { employees: [], departments: [] };
            this.state.total = data.total || 0;
            if (this.state.datePreset !== "none") { this.state.dateFrom = data.date_from; this.state.dateTo = data.date_to; }
        } catch (error) { this.notification.add("Failed to load attendance data.", { type: "danger" }); throw error; }
        finally { this.state.loading = false; }
    }
    async applyFilters() {
        this.state.page = 1; this.state.detailLevel = ""; this.state.selectedDepartmentId = 0;
        this.state.selectedDepartmentName = ""; this.state.selectedEmployeeId = 0;
        await this.loadData();
    }
    async changeSource(value) { this.state.source = value; this.state.sourceOpen = false; await this.applyFilters(); }
    async changeStatus(value) { this.state.status = value; this.state.statusOpen = false; await this.applyFilters(); }
    toggleEmployee(id) { const index = this.state.employeeIds.indexOf(id); if (index >= 0) this.state.employeeIds.splice(index, 1); else this.state.employeeIds.push(id); }
    toggleDepartment(id) { const index = this.state.departmentIds.indexOf(id); if (index >= 0) this.state.departmentIds.splice(index, 1); else this.state.departmentIds.push(id); }
    async clearEmployees() { this.state.employeeIds = []; this.state.employeeSearch = ""; this.state.employeeOpen = false; await this.applyFilters(); }
    async clearDepartments() { this.state.departmentIds = []; this.state.departmentSearch = ""; this.state.departmentOpen = false; await this.applyFilters(); }
    async doneEmployees() { this.state.employeeOpen = false; await this.applyFilters(); }
    async doneDepartments() { this.state.departmentOpen = false; await this.applyFilters(); }
    async clearFilters() { await this.resetFilters(); }
    async resetFilters() {
        const today = new Date();
        this.state.datePreset = "current_month"; this.state.dateMode = "month";
        this.state.dateFrom = ""; this.state.dateTo = ""; this.state.customDateFrom = ""; this.state.customDateTo = "";
        this.state.viewYear = today.getFullYear(); this.state.viewMonth = today.getMonth(); this.state.viewQuarter = Math.floor(today.getMonth() / 3);
        this.state.source = "attendance"; this.state.status = "all"; this.state.employeeIds = []; this.state.departmentIds = [];
        this.state.employeeSearch = ""; this.state.departmentSearch = ""; this.state.viewMode = "overview";
        this.closeFilters(); await this.applyFilters();
    }
    async previousPage() { if (this.state.page > 1) { this.state.page--; await this.loadData(); } }
    async nextPage() { if (this.state.page < this.pageCount) { this.state.page++; await this.loadData(); } }
    async exportExcel() {
        if (this.state.exporting) return;
        this.state.exporting = true;
        try {
            let mode = this.state.viewMode;
            let departmentId = false, employeeId = false;
            if (this.state.detailLevel === "department_employees") { mode = "employee"; departmentId = this.state.selectedDepartmentId; }
            else if (this.state.detailLevel === "employee_daily") {
                mode = "daily"; employeeId = this.state.selectedEmployeeId;
                departmentId = this.state.viewMode === "department" ? this.state.selectedDepartmentId : false;
            }
            const result = await this.orm.call("attendance.analysis.dashboard", "export_excel", [this.filters, mode, departmentId, employeeId]);
            const link = document.createElement("a"); link.href = result.url; document.body.appendChild(link); link.click(); link.remove();
            this.notification.add("Excel export is ready.", { type: "success" });
        } catch (error) { this.notification.add("Excel export failed.", { type: "danger" }); throw error; }
        finally { this.state.exporting = false; }
    }
    statusClass(status) {
        return { "Present": "aad-present", "Late In": "aad-warning", "Early Out": "aad-warning", "Late In / Early Out": "aad-warning", "Absent": "aad-danger", "Missing Check-Out": "aad-danger", "Leave": "aad-leave", "Weekend": "aad-weekend", "Public Holiday": "aad-holiday", "In Progress": "aad-holiday", "No Contract": "aad-weekend" }[status] || "aad-weekend";
    }
}
registry.category("actions").add("attendance_analysis_dashboard", AttendanceDashboard);