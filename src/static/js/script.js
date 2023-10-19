
jQuery(document).ready(function(){
    jQuery('#config select').change(function(e) {
        var obj = jQuery(e.target);
        var key = obj.attr('name');
        var val = obj.val();
        switch(key) {
            case 'count':
                val = parseInt(val)
                break;
            case 'bright':
                val = parseFloat(val)
                break;
        }
        set_config(key, val);
    });
    jQuery('#chase select').change(function(e) {
        var obj = jQuery(e.target);
        var key = obj.attr('name');
        var val = obj.val();
        switch(key) {
            case 'colours':
                val = JSON.parse(val);
                break;
        }
        set_effect_config('chase', key, val);
    });
    jQuery('#colour select').change(function(e) {
        var obj = jQuery(e.target);
        var key = obj.attr('name');
        var val = obj.val();
        switch(key) {
            case 'colour':
                val = JSON.parse(val);
                break;
        }
        set_effect_config('colour', key, val);
    });
    get_effects();
    get_config();
});

function get_effects() {
    jQuery.ajax({
        url: '/api/v1/effect',
        dataType: 'json',
        method: 'GET',
        success: function(data, textStatus, jqXHR) {
            //jQuery('#effect').text(JSON.stringify(data));
        }
    });
}

function get_config() {
    jQuery.ajax({
        url: '/api/v1/config',
        dataType: 'json',
        method: 'GET',
        success: function(data, textStatus, jqXHR) {
            process_config(data);
        }
    });
}

function process_config(data) {
    //jQuery('#config').text(JSON.stringify(data));
    jQuery('select[name="pin"]').val(data['pin']);
    jQuery('select[name="count"]').val(data['count']);
    jQuery('select[name="order"]').val(data['order']);
    jQuery('select[name="bright"]').val(data['bright']);
    var effect = data['selected_effect'];
    jQuery('select[name="selected_effect"]').val(effect);
    jQuery('.effects').hide();
    var obj = jQuery('#'+effect);
    obj.show();
    get_effect_config(data['selected_effect']);
}

function process_effect_config(effect, data) {
    //jQuery('#effect-config').text(JSON.stringify(data));
    if (effect = 'chase' && data['colours']) {
        var val = JSON.stringify(data['colours']).replace(new RegExp(",", "g"), ", ");
        jQuery('#chase select[name="colours"]').val(val);
    }
    if (effect = 'colour' && data['colour']) {
        var val = JSON.stringify(data['colour']).replace(new RegExp(",", "g"), ", ");
        jQuery('#colour select[name="colour"]').val(val);
    }
}

function set_config(key, val) {
    jQuery.ajax({
        url: '/api/v1/config/' + key,
        data: JSON.stringify({ value: val }),
        dataType: 'json',
        method: 'PUT',
        success: function(data, textStatus, jqXHR) {
            if (data['error']) {
                alert(data['error']);
            } else {
                process_config(data);
            }
        }
    });
}

function set_effect_config(effect, key, val) {
    jQuery.ajax({
        url: '/api/v1/effect/' + effect + '/' + key,
        data: JSON.stringify({ value: val }),
        dataType: 'json',
        method: 'PUT',
        success: function(data, textStatus, jqXHR) {
            if (data['error']) {
                alert(data['error']);
            } else {
                process_effect_config(effect, data);
            }
        }
    });
}

function get_effect_config(effect) {
    jQuery.ajax({
        url: '/api/v1/effect/' + effect,
        dataType: 'json',
        method: 'GET',
        success: function(data, textStatus, jqXHR) {
            process_effect_config(effect, data);
        }
    });
}

function show_confirm() {
    jQuery('#confirmModalCenter').modal('show');
}

function hide_confirm() {
    jQuery('#confirmModalCenter').modal('hide');
}

function really_shutdown() {
    jQuery.ajax({
        url: '/api/v1/shutdown',
        dataType: 'json',
        method: 'PUT',
        success: function(data, textStatus, jqXHR) {
            hide_confirm();
        }
    });
}

