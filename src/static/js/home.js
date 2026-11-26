const IMAGE_BASE = "https://image.tmdb.org/t/p/";

const collections = [
    {
        endpoint: "trending",
        element: "trending-grid"
    },
    {
        endpoint: "popular",
        element: "popular-grid"
    },
    {
        endpoint: "top-rated",
        element: "top-rated-grid"
    },
    {
        endpoint: "upcoming",
        element: "upcoming-grid"
    }
];

const movieCollections = {};

async function loadMovies(category, elementId) {
    const container = document.getElementById(elementId);

    try {
        const response = await fetch(`/movies/${category}`);

        if (!response.ok) {
            throw new Error("Unable to load movies.");
        }

        const data = await response.json();

        movieCollections[category] = data.movies;

        renderMovies(data.movies, container);

        if (category === "trending" && data.movies.length > 0) {
            updateHero(data.movies[0]);
        }

    } catch (error) {
        container.innerHTML = `
            <p class="error-message">
                Unable to load movies. Please try again later.
            </p>
        `;
        console.error(error);
    }
}


function renderMovies(movies, container) {
    if (!movies.length) {
        container.innerHTML = "<p>No movies available.</p>";
        return;
    }

    container.innerHTML = movies.map(movie => {
        const poster = movie.poster_path
            ? `${IMAGE_BASE}w500${movie.poster_path}`
            : null;

        const year = movie.release_date
            ? movie.release_date.substring(0, 4)
            : "N/A";

        return `
            <article class="movie-card">

                <div class="poster-wrapper">
                    ${
                        poster
                        ? `<img src="${poster}"
                               alt="${escapeHTML(movie.title)}"
                               loading="lazy">`
                        : `<div class="poster-placeholder">NO POSTER</div>`
                    }

                    <div class="poster-overlay">
                        <span>★ ${Number(movie.vote_average || 0).toFixed(1)}</span>
                    </div>
                </div>

                <div class="movie-info">
                    <h3>${escapeHTML(movie.title)}</h3>
                    <div class="movie-meta">
                        <span>${year}</span>
                        <span>★ ${Number(movie.vote_average || 0).toFixed(1)}</span>
                    </div>
                </div>

            </article>
        `;
    }).join("");
}


function updateHero(movie) {
    const hero = document.getElementById("hero-image");

    const backdrop = movie.backdrop_path
        ? `${IMAGE_BASE}original${movie.backdrop_path}`
        : null;

    if (backdrop) {
        hero.style.backgroundImage =
            `linear-gradient(90deg, rgba(16,17,22,.1), rgba(16,17,22,.15)), url("${backdrop}")`;
    }

    document.getElementById("hero-title").textContent = movie.title;

    document.getElementById("hero-year").textContent =
        movie.release_date?.substring(0, 4) || "";

    document.getElementById("hero-rating").textContent =
        `★ ${Number(movie.vote_average || 0).toFixed(1)} / 10`;
}


function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


document.getElementById("movie-search").addEventListener(
    "input",
    event => {
        const query = event.target.value.toLowerCase().trim();

        collections.forEach(collection => {
            const movies = movieCollections[collection.endpoint] || [];

            const filtered = movies.filter(movie =>
                movie.title.toLowerCase().includes(query)
            );

            renderMovies(
                filtered,
                document.getElementById(collection.element)
            );
        });
    }
);


collections.forEach(collection => {
    loadMovies(collection.endpoint, collection.element);
});