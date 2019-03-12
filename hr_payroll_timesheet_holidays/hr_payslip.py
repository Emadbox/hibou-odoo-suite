from odoo import models, api
from odoo.addons.hr_holidays.models.hr_holidays import HOURS_PER_DAY


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        leaves = {}

        for contract in contracts.filtered(lambda c: c.paid_hourly_timesheet):
            for leave in self._fetch_valid_leaves_timesheet(contract.employee_id.id, date_from, date_to):
                leave_code = self._create_leave_code(leave.holiday_status_id.name)
                if leave_code in leaves:
                    leaves[leave_code]['number_of_days'] += leave.number_of_days_temp
                    leaves[leave_code]['number_of_hours'] += leave.number_of_days_temp * HOURS_PER_DAY
                else:
                    leaves[leave_code] = {
                        'name': leave.holiday_status_id.name,
                        'sequence': 15,
                        'code': leave_code,
                        'number_of_days': leave.number_of_days_temp,
                        'number_of_hours': leave.number_of_days_temp * HOURS_PER_DAY,
                        'contract_id': contract.id,
                    }

        res = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        res.extend(leaves.values())
        return res

    @api.multi
    def action_payslip_done(self):
        for slip in self.filtered(lambda s: s.contract_id.paid_hourly_timesheet):
            leaves = self._fetch_valid_leaves_timesheet(slip.employee_id.id, slip.date_from, slip.date_to)
            leaves.write({'payslip_status': True})
        return super(HrPayslip, self).action_payslip_done()

    def _fetch_valid_leaves_timesheet(self, employee_id, date_from, date_to):
        valid_leaves = [
            ('employee_id', '=', employee_id),
            ('state', '=', 'validate'),
            ('date_from', '>=', date_from),
            ('date_from', '<=', date_to),
            ('payslip_status', '=', False),
            ('type', '=', 'remove'),
        ]

        return self.env['hr.holidays'].search(valid_leaves)

    def _create_leave_code(self, name):
        return 'L_' + name.replace(' ', '_')
