document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("top-movie-search");
    const resultsContainer = document.getElementById("top-movie-search-results");
    const selectedContainer = document.getElementById("selected-top-movies");
    const hiddenInput = document.getElementById("top-movies-data");

    if (!searchInput || !resultsContainer || !selectedContainer || !hiddenInput) {
        return;
    }

    const IMAGE_BASE = "https://image.tmdb.org/t/p/w342";

    let selectedMovies = [];

    try {
        const parsed = JSON.parse(hiddenInput.value || "[]");

        if (Array.isArray(parsed)) {
            selectedMovies = parsed
                .filter(movie => movie && typeof movie === "object" &&
                    movie.tmdb_id && movie.title)
                .slice(0, 5);
        }
    } catch (error) {
        console.error("Could not load saved Top 5 movies:", error);
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[character]);
    }

    function syncHiddenInput() {
        hiddenInput.value = JSON.stringify(selectedMovies);
    }

    function renderSelectedMovies() {
        selectedContainer.innerHTML = "";

        selectedMovies.forEach((movie, index) => {
            const card = document.createElement("div");
            card.className = "selected-top-movie";

            const poster = movie.poster_path
                ? `${IMAGE_BASE}${movie.poster_path}`
                : "";

            card.innerHTML = `
                ${poster
                    ? `<img src="${escapeHTML(poster)}" alt="${escapeHTML(movie.title)} poster">`
                    : `<div class="top-movie-no-poster">No poster</div>`
                }
                <button type="button"
                    class="remove-top-movie"
                    data-index="${index}"
                    aria-label="Remove ${escapeHTML(movie.title)}">×</button>
                <h4>${escapeHTML(movie.title)}</h4>
            `;

            selectedContainer.appendChild(card);
        });

        syncHiddenInput();
    }

    function renderResults(movies) {
        resultsContainer.innerHTML = "";

        if (!movies.length) {
            resultsContainer.innerHTML =
                '<p class="top-movie-message">No movies found.</p>';
            return;
        }

        movies.forEach(movie => {
            const alreadySelected = selectedMovies.some(
                selected => Number(selected.tmdb_id) === Number(movie.tmdb_id)
            );

            const result = document.createElement("div");
            result.className = "top-movie-result";

            const poster = movie.poster_path
                ? `${IMAGE_BASE}${movie.poster_path}`
                : "";

            result.innerHTML = `
                ${poster
                    ? `<img src="${escapeHTML(poster)}" alt="">`
                    : `<div class="top-movie-no-poster">No poster</div>`
                }
                <div class="top-movie-result-info">
                    <h4>${escapeHTML(movie.title)}</h4>
                    <span>${escapeHTML(
                        movie.release_date
                            ? movie.release_date.slice(0, 4)
                            : "Release year unknown"
                    )}</span>
                </div>
                <span>${alreadySelected ? "Added ✓" : "＋"}</span>
            `;

            if (!alreadySelected) {
                result.addEventListener("click", () => {
                    if (selectedMovies.length >= 5) {
                        alert("You can select a maximum of 5 movies.");
                        return;
                    }

                    selectedMovies.push({
                        tmdb_id: movie.tmdb_id,
                        title: movie.title,
                        poster_path: movie.poster_path
                    });

                    renderSelectedMovies();
                    renderResults(movies);
                });
            }

            resultsContainer.appendChild(result);
        });
    }

    let searchTimeout;

    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);

        const query = searchInput.value.trim();

        if (!query) {
            resultsContainer.innerHTML = "";
            return;
        }

        searchTimeout = setTimeout(async () => {
            resultsContainer.innerHTML =
                '<p class="top-movie-message">Searching...</p>';

            try {
                const response = await fetch(
                    `/movies/search?q=${encodeURIComponent(query)}`
                );

                if (!response.ok) {
                    throw new Error("Movie search failed.");
                }

                const data = await response.json();
                renderResults(data.movies || []);
            } catch (error) {
                console.error(error);
                resultsContainer.innerHTML =
                    '<p class="top-movie-message">Could not search movies. Please try again.</p>';
            }
        }, 350);
    });

    selectedContainer.addEventListener("click", event => {
        const button = event.target.closest(".remove-top-movie");

        if (!button) return;

        const index = Number(button.dataset.index);
        selectedMovies.splice(index, 1);

        renderSelectedMovies();

        if (searchInput.value.trim()) {
            searchInput.dispatchEvent(new Event("input"));
        }
    });

    renderSelectedMovies();
});
