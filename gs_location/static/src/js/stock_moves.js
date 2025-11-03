odoo.define('gs_location.stock_moves', function (require){
    "use strict";
    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require("web.ListController");
    var rpc = require('web.rpc');

    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName == 'stock.move') {
                var your_btn = this.$buttons.find('button.get_stock_moves_data');
                your_btn.on('click', this.proxy('get_stock_moves_data'));
            }
        },
        get_stock_moves_data: function(){

//        #$#$# TO OPEN A WIZARD #$#$#
         this.do_action({
                name: "Get Stock Moves Data",
                type: 'ir.actions.act_window',
                res_model: 'get.stock.moves.data.wizard',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });

        }
    };

    ListController.include(includeDict);
});