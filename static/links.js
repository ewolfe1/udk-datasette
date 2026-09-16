// Opens external links in a new tab.
// "External" = the href has a different host than the current page.
// Runs once at DOMContentLoaded; ~5 ms even on a page with hundreds of links.
document.addEventListener("DOMContentLoaded", function () {
    var here = window.location.host;
    var links = document.querySelectorAll("a[href^='http']");
    for (var i = 0; i < links.length; i++) {
        try {
            if (new URL(links[i].href).host !== here) {
                links[i].target = "_blank";
                links[i].rel = "noopener noreferrer";
            }
        } catch (e) { /* malformed href — ignore */ }
    }
});
