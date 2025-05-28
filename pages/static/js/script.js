function filterCountries() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let items = document.querySelectorAll("#countriesList li");

    items.forEach(function(item) {
        let text = item.textContent.toLowerCase();
        if (text.includes(input)) {
            item.style.display = "block";
        } else {
            item.style.display = "none";
        }
    });
}
