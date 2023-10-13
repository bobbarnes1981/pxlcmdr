
jQuery(document).ready(function(){
    jQuery('h1').css("color", "red");
    get_effects();
    get_config();
});

function get_effects() {
    jQuery.ajax({
        url: '/api/v1/effect',
        dataType: 'json',
        method: 'GET',
        success: function(data, textStatus, jqXHR) {
            jQuery('#effect').text(JSON.stringify(data));
        }
    });
}

function get_config() {
    jQuery.ajax({
        url: '/api/v1/config',
        dataType: 'json',
        method: 'GET',
        success: function(data, textStatus, jqXHR) {
            jQuery('#config').text(JSON.stringify(data));
            get_effect_config(data['selected_effect']);
        }
    });
}

function get_effect_config(effect) {
    jQuery.ajax({
        url: '/api/v1/effect/' + effect,
        dataType: 'json',
        method: 'GET',
        success: function(data, textStatus, jqXHR) {
            jQuery('#effect-config').text(JSON.stringify(data));
        }
    });
}

function shutdown() {
    // TODO: bootstrap dialog?
    if (confirm('Shutdown?')) {
        jQuery.ajax({
            url: '/api/v1/shutdown',
            dataType: 'json',
            method: 'PUT',
            success: function(data, textStatus, jqXHR) {
                alert('shutting down...');
            }
        });
    }
}

