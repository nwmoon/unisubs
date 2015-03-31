(function() {

$(document).ready(function() {
    $('a.menu-toggle').click(function() {
        var menuId = $(this).data('menu');
        $('#' + menuId).toggle();
    });
});
}(this));
