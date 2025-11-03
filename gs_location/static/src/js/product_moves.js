odoo.define('gs_location.product_moves', function (require){
    "use strict";
    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require("web.ListController");
    var rpc = require('web.rpc');

    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName == 'stock.move.line') {
                var your_btn = this.$buttons.find('button.get_product_moves_data');
                your_btn.on('click', this.proxy('get_product_moves_data'));
            }
        },
        get_product_moves_data: function(){

//        #$#$# TO OPEN A WIZARD #$#$#
         this.do_action({
                name: "Get Product Moves Data",
                type: 'ir.actions.act_window',
                res_model: 'get.product.moves.data.wizard',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });

        }
    };

    ListController.include(includeDict);
});