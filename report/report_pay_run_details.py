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
        empolyee_obj = self.pool.get('hr.employee')
        payslip = self.pool.get('hr.payslip')

        def get_recursive_parent(current_rule_category, rule_categories = None):
            if rule_categories:
                rule_categories = current_rule_category | rule_categories
            else:
                rule_categories = current_rule_category

            if current_rule_category.parent_id:
                return get_recursive_parent(current_rule_category.parent_id, rule_categories)
            else:
                return rule_categories

        finalResult = []
        result = {}
        plIdToLineIds = {}
        plIds = []
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
            stt = 0
            for id  in plIdToLineIds:
                # loop tung Payslip id
                payslipres = payslip.browse(self.cr, self.uid, id)
                employee_id = payslipres.employee_id
                employee_id = empolyee_obj.browse(self.cr, self.uid, employee_id.id, context=None)
                employee_name = employee_id.name
                job_name = employee_id.job_id.name
                employee_wage = employee_id.contract_id.wage
                ngay_cong = tang_ca = nghi_cho_viec = tre_vao_ra = tre_ko_ly_do = nghi_ko_phep = 0
                sql = '''select code, amount from hr_payslip_input where payslip_id = %d'''%id
                self.cr.execute(sql)
                for code, amount in self.cr.fetchall():
                    if code == 'NGAY_CONG':
                        ngay_cong = amount
                    elif code == 'TANG_CA':
                        tang_ca = amount
                    elif code == 'NGHI_CHO_VIEC':
                        nghi_cho_viec = amount
                    elif code == 'TRE_VAO_RA':
                        tre_vao_ra = amount
                    elif code == 'TRE_KHONG_LY_DO':
                        tre_ko_ly_do = amount
                    elif code == 'NGHI_KHONG_PHEP':
                        nghi_ko_phep = amount
                luong_ngay_cong = luong_tang_ca = luong_nghi_cho_viec = tong_luong = 0
                # Cac khoan phu cap
                pc_trach_nhiem = pc_kiem_nhiem = pc_com = pc_chuyen_can = pc_khac = tong_phu_cap = 0
                # luong san pham
                luong_san_pham = 0
                tong_cac_khoan_cong = 0
                #Cac khoan tru
                tru_vi_pham = tru_nghi_ko_phep = tru_tre_ko_ly_do = tru_tre_vao_ra = tru_bhxh_bhyt_bhtn = tru_dn_dong_bh = 0
                tong_cac_khoan_tru = 0
                luong_thuc_lanh = 0       
                
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
                    for key, value in result.iteritems():
                        rule_categories = rule_cate_obj.browse(self.cr, self.uid, [key])
                        parents = get_recursive_parent(rule_categories)
                        category_total = 0
                        for line in payslip_line.browse(self.cr, self.uid, value):
                            category_total += line.total
                        for parent in parents:
                            if parent.code == 'LUONG_SAN_PHAM':
                                luong_san_pham = category_total
                            elif parent.code == 'LUONG_NGAY_CONG':
                                tong_luong = category_total
                            elif parent.code == 'PHU_CAP':
                                tong_phu_cap = category_total
                            elif parent.code == 'KHOAN_TRU':
                                tong_cac_khoan_tru = category_total
                            elif parent.code == 'TONG_KHOAN_CONG':
                                tong_cac_khoan_cong = category_total
                            elif parent.code == 'TONG_KHOAN_TRU':
                                tong_cac_khoan_tru = category_total
                            elif parent.code == 'LUONG_THUC_LANH':
                                luong_thuc_lanh = category_total
                                
                        for line in payslip_line.browse(self.cr, self.uid, value):
                            ma_ct = line.code
                            tongcong = line.total
                            if ma_ct == 'CT_LUONG_NGAY_CONG':
                                luong_ngay_cong = tongcong
                            elif ma_ct == 'CT_LUONG_TANG_CA':
                                luong_tang_ca = tongcong
                            elif ma_ct == 'CT_LUONG_NGHI_CHO_VIEC':
                                luong_nghi_cho_viec = tongcong
                            elif ma_ct == 'CT_PHU_CAP_TRACH_NHIEM':
                                pc_trach_nhiem = tongcong
                            elif ma_ct == 'CT_PHU_CAP_KIEM_NHIEM':
                                pc_kiem_nhiem = tongcong
                            elif ma_ct == 'CT_PHU_CAP_COM':
                                pc_com = tongcong
                            elif ma_ct == 'CT_PHU_CAP_CHUYEN_CAN':
                                pc_chuyen_can = tongcong
                            elif ma_ct == 'CT_PHU_CAP_KHAC':
                                pc_khac = tongcong
                            elif ma_ct == 'CT_TRU_VI_PHAM':
                                tru_vi_pham = tongcong
                            elif ma_ct == 'CT_NGHI_KHONG_PHEP':
                                tru_nghi_ko_phep = tongcong
                            elif ma_ct == 'CT_TRE_KHONG_LY_DO':
                                tru_tre_ko_ly_do = tongcong
                            elif ma_ct == 'CT_TRE_VR':
                                tru_tre_vao_ra = tongcong
                            elif ma_ct == 'CT_BAO_HIEM':
                                tru_bhxh_bhyt_bhtn = tongcong
                stt +=1
                finalResult.append({
                        'stt':stt,
                        'ho_ten':employee_name,
                        'chuc_danh':job_name,
                        'luong_co_ban':employee_wage,
                        'ngay_cong':ngay_cong,
                        'tang_ca':tang_ca,
                        'nghi_cho_viec':nghi_cho_viec,
                        'tre_vao_ra':tre_vao_ra,
                        'tre_ko_ly_do':tre_ko_ly_do,
                        'nghi_ko_phep':nghi_ko_phep,
                        'luong_ngay_cong':luong_ngay_cong,
                        'luong_tang_ca':luong_tang_ca,
                        'luong_nghi_cho_viec':luong_nghi_cho_viec,
                        'tong_luong':tong_luong,
                        'pc_trach_nhiem':pc_trach_nhiem,
                        'pc_kiem_nhiem':pc_kiem_nhiem,
                        'pc_com':pc_com,
                        'pc_chuyen_can':pc_chuyen_can,
                        'pc_khac':pc_khac,
                        'tong_phu_cap':tong_phu_cap,
                        'luong_san_pham':luong_san_pham,
                        'tong_cac_khoan_cong':tong_cac_khoan_cong,
                        'tru_vi_pham':tru_vi_pham,
                        'tru_nghi_ko_phep':tru_nghi_ko_phep,
                        'tru_tre_ko_ly_do':tru_tre_ko_ly_do,
                        'tru_tre_vao_ra':tru_tre_vao_ra,
                        'tru_bhxh_bhyt_bhtn':tru_bhxh_bhyt_bhtn,
                        'tru_dn_dong_bh':tru_dn_dong_bh,
                        'tong_cac_khoan_tru':tong_cac_khoan_tru,
                        'luong_thuc_lanh':luong_thuc_lanh
                    })            
        return finalResult


class wrapped_report_payrundetails(osv.AbstractModel):
    _name = 'report.hr_payroll.report_payrundetails'
    _inherit = 'report.abstract_report'
    _template = 'hr_payroll.report_payrundetails'
    _wrapped_report_class = pay_run_details_report
