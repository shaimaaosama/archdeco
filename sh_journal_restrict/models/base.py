from  odoo import models,api



class Model(models.AbstractModel):
    _inherit = 'base'


    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        # Include user in cache key since readonly logic depends on current user's analytic ids
        key = super()._get_view_cache_key(view_id=view_id, view_type=view_type, **options)
        return key + (self.env.uid,)

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)

        if view_type == 'form':
            user = self.env.user
            allowed = user.journal_ids.ids

            # Modify the form XML
            for node in arch.xpath("//field[@name='journal_id']"):

                expr = (
                    "journal_id "
                    "and journal_id not in %s"
                ) % allowed
                if allowed:
                    for node in arch.xpath("//field[@name='journal_id']"):
                        # set a proper domain list
                        domain = f"[('id', 'in', {allowed})]"
                        node.set('domain', domain)
                node.set('readonly', expr)

                # Also update the JS modifiers so the client enforces readonly
                import json
                modifiers = node.get('modifiers')
                if modifiers:
                    mods = json.loads(modifiers)
                else:
                    mods = {}
                mods['readonly'] = True
                node.set('modifiers', json.dumps(mods))

        return arch, view