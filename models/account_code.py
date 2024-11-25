import peewee

from . import db

class AccountCode(peewee.Model):
    account_code = peewee.TextField()
    level = peewee.IntegerField()
    description = peewee.TextField()
    uom = peewee.TextField()
    uom2 = peewee.TextField()
    metric_uom = peewee.TextField()
    metric_uom2 = peewee.TextField()
    notes = peewee.TextField()
    personal_notes = peewee.TextField(null=True)
    _flags = peewee.BitField()
    has_labor_cost = _flags.flag(1)
    has_const_eqp_cost = _flags.flag(2)
    has_fom_rented_eqp_cost = _flags.flag(4)
    has_supplies_cost = _flags.flag(8)
    has_materials_cost = _flags.flag(16)
    has_subcontract_cost = _flags.flag(32)
    has_fixed_fees_and_services_cost = _flags.flag(64)
    has_contingency_allowances_cost = _flags.flag(128)
    has_ga_cost = _flags.flag(256)
    uom_to_sup_uom = _flags.flag(512)
    uom_to_sup_uom2 = _flags.flag(1024)
    uom2_to_sup_uom2 = _flags.flag(2048)
    auto_quantity_uom = _flags.flag(4096)
    auto_quantity_uom2 = _flags.flag(8192)

    class Meta:
        database = db