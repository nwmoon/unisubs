(function() {

var activeMenu = null;

function openMenu(linkElt) {
    var menuId = linkElt.data('menu');
    $('#' + menuId).show();
    linkElt.addClass('open');
    activeMenu = linkElt;
}
function closeMenu() {
    var menuId = activeMenu.data('menu');
    $('#' + menuId).hide();
    activeMenu.removeClass('open');
    activeMenu = null;
}

$(document).ready(function() {
    $('a.menu-toggle').click(function() {
        var linkElt = $(this);
        if(activeMenu === null) {
            openMenu(linkElt);
        } else if (activeMenu[0] == linkElt[0]) {
            closeMenu();
        } else {
            closeMenu();
            openMenu(linkElt);
        }
    });
});
}(this));
