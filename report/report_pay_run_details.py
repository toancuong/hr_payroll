#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import osv
from openerp.report import report_sxw


class pay_run_details_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(pay_run_details_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                    'get_details_run_by_rule_category': self.get_details_run_by_rule_category,
                })
    def get_details_run_by_rule_category(self, obj):
        payslip_line = self.pool.get('hr.payslip.line')
        rule_cate_obj = self.pool.get('hr.salary.rule.category')

        def get_recursive_parent(current_rule_category, rule_categories = None):
            if rule_categories:
                rule_categories = current_rule_category | rule_categories
            else:
                rule_categories = current_rule_category

            if current_rule_category.parent_id:
                return get_recursive_parent(current_rule_category.parent_id, rule_categories)
            else:
                return rule_categories

        res = []
        result = {}
        plIdToLineIds = {}
        plIds = []
        not_show_category =['LUONG_NGAY_CONG','PHU_CAP','KHOAN_TRU','LUONG_SAN_PHAM']
        for id in range(len(obj)):
            plIds.append(obj[id].id)
        if plIds:
            self.cr.execute('''SELECT pl.id, pl_line.id FROM hr_payslip as pl
                LEFT JOIN hr_payslip_line AS pl_line on (pl.id = pl_line.slip_id) 
                WHERE pl.id in %s
                GROUP BY pl.id, pl_line.id''',(tuple(plIds),))
            res = self.cr.fetchall()
            for id in plIds:
                plIdToLineIds.setdefault(id, [])
            for r in res:
                plIdToLineIds[r[0]].append(r[1])
            for id  in plIdToLineIds:
                # loop tung P
                lineIds = plIdToLineIds[id]
                if lineIds:
                    self.cr.execute('''SELECT pl.id, pl.category_id FROM hr_payslip_line as pl \
                        LEFT JOIN hr_salary_rule_category AS rc on (pl.category_id = rc.id) \
                        WHERE pl.id in %s \
                        GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id \
                        ORDER BY pl.sequence, rc.parent_id''',(tuple(lineIds),))
                    for x in self.cr.fetchall():
                        result.setdefault(x[1], [])
                        result[x[1]].append(x[0])
                    no = 1
                    for key, value in result.iteritems():
                        rule_categories = rule_cate_obj.browse(self.cr, self.uid, [key])
                        parents = get_recursive_parent(rule_categories)
                        category_total = 0
                        for line in payslip_line.browse(self.cr, self.uid, value):
                            category_total += line.total
                        level = 0
                        isSP = False
                        for parent in parents:
                            if parent.code == 'LUONG_SAN_PHAM':
                                isSP = True
                                continue
                            if parent.code in not_show_category:
                                res.append({
                                'no':"",
                                'rule_category': parent.name,
                                'name': parent.name,
                                'code': parent.code,
                                'level': 3,
                                'total': category_total,
                                })
                                continue
                            res.append({
                                'no':"",
                                'rule_category': parent.name,
                                'name': parent.name,
                                'code': parent.code,
                                'level': level,
                                'total': category_total,
                            })
                        if len(value) <= 1 and not isSP:
                            continue
                        level += 1
                        for line in payslip_line.browse(self.cr, self.uid, value):
                            no += 1
                            self.cr.execute("SELECT input.code FROM hr_salary_rule as rule, hr_rule_input as input\
                                            WHERE rule.id = input.input_id and rule.code = %s",(line.code,))
                            rule_input_code = self.cr.fetchone()
                            amount = '-'
                            if rule_input_code:
                                self.cr.execute("SELECT amount FROM hr_payslip_input WHERE code = %s",(rule_input_code,))
                                for (item_id,) in self.cr.fetchall():
                                    amount = item_id
                                    break
                            
                            res.append({
                                'no': no,
                                'rule_category': line.name,
                                'name': line.name,
                                'code': line.code,
                                'amount': amount,
                                'total': line.total,
                                'level': level
                            })
        return res


class wrapped_report_payrundetails(osv.AbstractModel):
    _name = 'report.hr_payroll.report_payrundetails'
    _inherit = 'report.abstract_report'
    _template = 'hr_payroll.report_payrundetails'
    _wrapped_report_class = pay_run_details_report
