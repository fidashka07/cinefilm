const IMAGE_BASE = "https://image.tmdb.org/t/p/";

const collections = [
    { endpoint: "trending", element: "trending-grid" },
    { endpoint: "popular", element: "popular-grid" },
    { endpoint: "top-rated", element: "top-rated-grid" },
    { endpoint: "upcoming", element: "upcoming-grid" }
];

const movieCollections = {};


// ========================================
// LOAD MOVIES
// ========================================

async function loadMovies(category, elementId) {
    const container = document.getElementById(elementId);

    try {
        const response = await fetch(`/movies/${category}`);

        if (!response.ok) {
            throw new Error("Unable to load movies.");
        }

        const data = await response.json();

        movieCollections[category] = data.movies || [];
        addHeroMovies();

        renderMovies(data.movies || [], container);

    } catch (error) {
        container.innerHTML = `
            <p class="error-message">
                Unable to load movies. Please try again later.
            </p>
        `;

        console.error(error);
    }
}


// ========================================
// RENDER FILMSTRIP
// ========================================

function renderMovies(movies, container, append = false) {
    if (!movies.length) {
        if (!append) {
            container.innerHTML = `
                <p class="loading">No movies found.</p>
            `;
        }
        return;
    }

    const startIndex = append ? container.children.length : 0;

    const cards = movies.map((movie, index) => {
        const poster = movie.poster_path
            ? `${IMAGE_BASE}w500${movie.poster_path}`
            : null;

        const year = movie.release_date
            ? movie.release_date.substring(0, 4)
            : "N/A";

        const rating = Number(movie.vote_average || 0).toFixed(1);

        return `
            <article
                class="movie-card"
                data-movie-id="${movie.tmdb_id}"
                tabindex="0"
                role="button"
                aria-label="View ${escapeHTML(movie.title)} details"
            >
                <div class="frame-number">
                    FRAME ${String(startIndex + index + 1).padStart(3, "0")}
                </div>

                <div class="poster-wrapper">
                    ${
                        poster
                        ? `
                            <img
                                src="${poster}"
                                alt="${escapeHTML(movie.title)}"
                                loading="lazy"
                            >
                        `
                        : `
                            <div class="poster-placeholder">NO POSTER</div>
                        `
                    }

                    <div class="poster-overlay">
                        <span>★ ${rating}</span>
                        <span class="view-film">VIEW FILM ↗</span>
                    </div>
                </div>

                <div class="movie-info">
                    <h3>${escapeHTML(movie.title)}</h3>

                    <div class="movie-meta">
                        <span>${year}</span>
                        <span>★ ${rating}</span>
                    </div>

                    <button
                        class="watchlist-btn"
                        data-watchlist-id="${movie.tmdb_id}"
                        type="button"
                    >＋ Watchlist</button>
                </div>
            </article>
        `;
    }).join("");

    if (append) {
        container.insertAdjacentHTML("beforeend", cards);
    } else {
        container.innerHTML = cards;
    }
}


// ========================================
// HERO
// ========================================

// ========================================
// FEATURED HERO — ATTACK ON TITAN
// ========================================

// ========================================
// AUTOMATIC FEATURED MOVIE SLIDER
// ========================================

const HERO_INTERVAL = 6500;

let heroMovies = [];
let currentHeroIndex = 0;
let heroTimer = null;

const ATTACK_ON_TITAN = {
    title: "Attack on Titan",
    release_date: "2013-04-07",
    vote_average: 8.7,
    overview: "Humanity's fight for survival begins behind the walls.",
    backdrop_path: "/rqbCbjB19amtOtFQbb3K2lgm2zv.jpg",
    category: "THE LEGENDARY SERIES"
};

function initializeHero() {
    const hero = document.getElementById("hero-image");

    if (!hero) return;

    heroMovies = [ATTACK_ON_TITAN];

    updateHeroSlide(0);
    startHeroTimer();

    document.getElementById("hero-next").addEventListener(
        "click",
        () => changeHeroSlide(1)
    );

    document.getElementById("hero-prev").addEventListener(
        "click",
        () => changeHeroSlide(-1)
    );

    hero.addEventListener("mouseenter", stopHeroTimer);
    hero.addEventListener("mouseleave", startHeroTimer);

    hero.addEventListener("focusin", stopHeroTimer);
    hero.addEventListener("focusout", startHeroTimer);
}


function addHeroMovies() {
    const categories = [
        ["trending", "TRENDING NOW"],
        ["popular", "POPULAR FILMS"],
        ["top-rated", "ALL-TIME GREATS"]
    ];

    const existingIds = new Set(
        heroMovies.map(movie => movie.tmdb_id)
    );

    categories.forEach(([category, label]) => {

        const movies = movieCollections[category] || [];

        movies.forEach(movie => {

            if (!movie.backdrop_path) return;

            if (existingIds.has(movie.tmdb_id)) return;

            existingIds.add(movie.tmdb_id);

            heroMovies.push({
                ...movie,
                category: label
            });

        });

    });

    renderHeroDots();

if (currentHeroIndex === 0) {
    updateHeroSlide(0);
}

startHeroTimer();
}


function updateHeroSlide(index) {
    if (!heroMovies.length) return;

    currentHeroIndex =
        (index + heroMovies.length) % heroMovies.length;

    const movie = heroMovies[currentHeroIndex];
    const hero = document.getElementById("hero-image");

    const backdrop = movie.backdrop_path
        ? `${IMAGE_BASE}original${movie.backdrop_path}`
        : "";

    hero.classList.add("is-transitioning");

    window.setTimeout(() => {

        if (backdrop) {
            hero.style.backgroundImage = `
                linear-gradient(
                    0deg,
                    rgba(12, 10, 15, 0.96),
                    rgba(12, 10, 15, 0.05) 75%
                ),
                url("${backdrop}")
            `;
        }

        document.getElementById("hero-title").textContent =
            movie.title;

        document.getElementById("hero-year").textContent =
            movie.release_date
                ? movie.release_date.substring(0, 4)
                : "COMING SOON";

        document.getElementById("hero-rating").textContent =
            `★ ${Number(movie.vote_average || 0).toFixed(1)} / 10`;

        document.getElementById("hero-overview").textContent =
            movie.overview || "Discover this film on CINEFILM.";

        document.getElementById("hero-label").textContent =
            movie.category || "FEATURED FILM";

        document.getElementById("hero-counter").textContent =
            `${String(currentHeroIndex + 1).padStart(2, "0")} / ${String(heroMovies.length).padStart(2, "0")}`;

        renderHeroDots();

        hero.classList.remove("is-transitioning");

    }, 250);
}


function changeHeroSlide(direction) {
    updateHeroSlide(currentHeroIndex + direction);
    restartHeroTimer();
}


function renderHeroDots() {
    const container = document.getElementById("hero-dots");
    if (!container) return;

    const maxDots = 7;
    const total = heroMovies.length;

    const start = Math.max(
        0,
        Math.min(currentHeroIndex - 3, total - maxDots)
    );

    const end = Math.min(total, start + maxDots);

    container.innerHTML = Array.from(
        { length: end - start },
        (_, i) => start + i
    ).map(index => `
        <button
            class="hero-dot ${index === currentHeroIndex ? "active" : ""}"
            aria-label="Show featured movie ${index + 1}"
            aria-current="${index === currentHeroIndex ? "true" : "false"}"
            data-index="${index}"
            type="button"
        ></button>
    `).join("");

    container.querySelectorAll(".hero-dot").forEach(dot => {
        dot.addEventListener("click", () => {
            updateHeroSlide(Number(dot.dataset.index));
            restartHeroTimer();
        });
    });
}


function startHeroTimer() {
    stopHeroTimer();

    if (heroMovies.length <= 1) return;

    heroTimer = window.setInterval(() => {
        updateHeroSlide(currentHeroIndex + 1);
    }, HERO_INTERVAL);
}


function stopHeroTimer() {
    if (heroTimer) {
        clearInterval(heroTimer);
        heroTimer = null;
    }
}


function restartHeroTimer() {
    startHeroTimer();
}

// ========================================
// FILM REEL INTERACTIONS
// ========================================

function initializeReels() {

    document.querySelectorAll(".film-track").forEach(track => {

        let isDragging = false;
        let startX = 0;
        let scrollStart = 0;

        // Mouse drag

        track.addEventListener("mousedown", event => {
            if (event.target.closest(".movie-card")) {
                return;
            }

            isDragging = true;
            startX = event.pageX;
            scrollStart = track.scrollLeft;

            track.classList.add("is-dragging");
        });

        window.addEventListener("mouseup", () => {
            isDragging = false;
            track.classList.remove("is-dragging");
        });

        track.addEventListener("mouseleave", () => {
            isDragging = false;
            track.classList.remove("is-dragging");
        });

        track.addEventListener("mousemove", event => {
            if (!isDragging) return;

            event.preventDefault();

            const distance = event.pageX - startX;

            track.scrollLeft = scrollStart - distance * 1.3;
        });

        // Mouse wheel -> horizontal movement

        track.addEventListener("wheel", event => {
            if (Math.abs(event.deltaY) > Math.abs(event.deltaX)) {
                event.preventDefault();

                track.scrollBy({
                    left: event.deltaY * 1.2,
                    behavior: "auto"
                });
            }
        }, { passive: false });

    });


    // Navigation arrows

    document.querySelectorAll(".reel-arrow").forEach(button => {

        button.addEventListener("click", () => {
            const section = button.closest(".movie-section");
            const track = section.querySelector(".film-track");

            const direction = Number(button.dataset.direction);

            track.scrollBy({
                left: direction * 550,
                behavior: "smooth"
            });
        });

    });
}


// ========================================
// MOVIE DETAILS MODAL
// ========================================

function createMovieModal() {
    const modal = document.createElement("div");

    modal.id = "movie-modal";
    modal.className = "movie-modal";

    modal.innerHTML = `
        <div class="modal-backdrop"></div>

        <div class="modal-content" role="dialog" aria-modal="true">

            <button class="modal-close" aria-label="Close">×</button>

            <div class="modal-body">
                <p class="loading">Loading film details...</p>
            </div>

        </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector(".modal-close").addEventListener(
        "click",
        closeMovieModal
    );

    modal.querySelector(".modal-backdrop").addEventListener(
        "click",
        closeMovieModal
    );

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            closeMovieModal();
        }
    });

    return modal;
}

const movieModal = createMovieModal();


function closeMovieModal() {
    movieModal.classList.remove("active");
    document.body.classList.remove("modal-open");
}


async function openMovieDetails(movieId) {
    if (!movieId) return;

    movieModal.classList.add("active");
    document.body.classList.add("modal-open");

    const body = movieModal.querySelector(".modal-body");

    body.innerHTML = `
        <p class="loading">Loading cinematic details...</p>
    `;

    try {
        const response = await fetch(`/movies/details/${movieId}`);

        if (!response.ok) {
            throw new Error("Unable to load movie details.");
        }

        const data = await response.json();

        const movie = data.movie || data;

        const backdrop = movie.backdrop_path
            ? `${IMAGE_BASE}original${movie.backdrop_path}`
            : "";

        const poster = movie.poster_path
            ? `${IMAGE_BASE}w500${movie.poster_path}`
            : "";

        const directors = (data.directors || [])
            .map(person => escapeHTML(person.name))
            .join(", ");

        const cast = (data.cast || [])
            .slice(0, 8)
            .map(person => escapeHTML(person.name))
            .join(" · ");

        const trailer = (data.trailers || []).find(
            video => video.site === "YouTube"
        );

        body.innerHTML = `
            <div
                class="modal-hero"
                style="${backdrop ? `background-image: url('${backdrop}')` : ""}"
            >
                <div class="modal-hero-overlay"></div>

                <div class="modal-title">
                    <span class="eyebrow">CINEFILM PRESENTS</span>
                    <h2>${escapeHTML(movie.title || "Untitled")}</h2>

                    <p>
                        ${movie.release_date?.substring(0, 4) || "N/A"}
                        · ★ ${Number(movie.vote_average || 0).toFixed(1)}
                    </p>
                </div>
            </div>

            <div class="modal-details">

                ${
                    poster
                    ? `<img class="modal-poster" src="${poster}" alt="">`
                    : ""
                }

                <div class="modal-description">
                    <span class="eyebrow">THE STORY</span>

                    <p>
                        ${escapeHTML(movie.overview || "No synopsis available.")}
                    </p>

                    <div class="user-rating-panel">
                        <span class="eyebrow">YOUR RATING</span>

                        ${
                            data.can_rate
                            ? `
                                <div
                                    class="rating-stars"
                                    data-tmdb-id="${movie.tmdb_id}"
                                    data-current-rating="${data.user_rating || 0}"
                                    role="group"
                                    aria-label="Rate this movie from 0.5 to 10"
                                >
                                    ${Array.from({ length: 20 }, (_, index) => {
                                        const score = (index + 1) / 2;
                                        const halfClass = index % 2 === 0
                                            ? "star-left"
                                            : "star-right";

                                        return `
                                            <button
                                                type="button"
                                                class="rating-half-star ${halfClass}"
                                                data-rating-value="${score}"
                                                aria-label="${score} out of 10"
                                                title="${score}/10"
                                            >★</button>
                                        `;
                                    }).join("")}
                                </div>

                                <div class="rating-feedback">
                                    <span class="rating-score">
                                        ${data.user_rating
                                            ? `${Number(data.user_rating).toFixed(1)} / 10`
                                            : "Choose your rating"}
                                    </span>

                                    <span class="rating-status" aria-live="polite"></span>
                                </div>
                            `
                            : `
                                <p class="rating-login-message">
                                    Log in to rate this movie.
                                </p>
                            `
                        }
                    </div>

                    ${
                        directors
                        ? `
                            <div class="detail-row">
                                <span>DIRECTOR</span>
                                <p>${directors}</p>
                            </div>
                        `
                        : ""
                    }

                    ${
                        cast
                        ? `
                            <div class="detail-row">
                                <span>STARRING</span>
                                <p>${cast}</p>
                            </div>
                        `
                        : ""
                    }

                    ${
                        trailer
                        ? `
                            <a
                                class="primary-btn trailer-btn"
                                href="https://www.youtube.com/watch?v=${encodeURIComponent(trailer.key)}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Watch trailer ↗
                            </a>
                        `
                        : ""
                    }
                </div>
            </div>
        `;

    } catch (error) {
        body.innerHTML = `
            <p class="error-message">
                Unable to load movie details. Please try again.
            </p>
        `;

        console.error(error);
    }
}

// ========================================
// ANIMATED MOVIE RATING
// ========================================

function updateRatingStars(container, score) {
    container.querySelectorAll(".rating-half-star").forEach(button => {
        const value = Number(button.dataset.ratingValue);

        button.classList.toggle("active", value <= score);
    });

    const scoreLabel = container
        .closest(".user-rating-panel")
        .querySelector(".rating-score");

    scoreLabel.textContent = score
        ? `${Number(score).toFixed(1)} / 10`
        : "Choose your rating";
}


movieModal.addEventListener("mouseover", event => {
    const button = event.target.closest(".rating-half-star");

    if (!button) return;

    const container = button.closest(".rating-stars");

    updateRatingStars(
        container,
        Number(button.dataset.ratingValue)
    );
});


movieModal.addEventListener("mouseleave", () => {
    const container = movieModal.querySelector(".rating-stars");

    if (!container) return;

    updateRatingStars(
        container,
        Number(container.dataset.currentRating)
    );
});


movieModal.addEventListener("click", async event => {
    const button = event.target.closest(".rating-half-star");

    if (!button) return;

    const container = button.closest(".rating-stars");
    const score = Number(button.dataset.ratingValue);
    const tmdbId = container.dataset.tmdbId;

    const panel = container.closest(".user-rating-panel");
    const status = panel.querySelector(".rating-status");

    if (!Number.isFinite(score) || !tmdbId) return;

    container.querySelectorAll("button").forEach(star => {
        star.disabled = true;
    });

    status.textContent = "Saving...";
    status.classList.remove("rating-success");

    try {
        const response = await fetch(`/movies/${tmdbId}/rating`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ score })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to save rating.");
        }

        container.dataset.currentRating = data.score;

        updateRatingStars(container, data.score);

        container.classList.remove("rating-celebrate");
        void container.offsetWidth;
        container.classList.add("rating-celebrate");

        status.textContent = "✓ Rating saved";
        status.classList.add("rating-success");

    } catch (error) {
        status.textContent = error.message;
    } finally {
        container.querySelectorAll("button").forEach(star => {
            star.disabled = false;
        });
    }
});

// Movie selection

document.addEventListener("click", event => {
    const card = event.target.closest(".movie-card");

    if (!card) return;

    openMovieDetails(card.dataset.movieId);
});

document.addEventListener("keydown", event => {
    const card = event.target.closest(".movie-card");

    if (!card) return;

    if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openMovieDetails(card.dataset.movieId);
    }
});


// ========================================
// SEARCH
// ========================================

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

            const container = document.getElementById(collection.element);

            renderMovies(filtered, container);
        });

    }
);


// ========================================
// INITIALIZATION
// ========================================

initializeReels();
initializeHero();

collections.forEach(collection => {
    loadMovies(collection.endpoint, collection.element);
});

// ========================================
// CINEFILM POPCORN LOADER
// ========================================

(() => {
    const loader = document.getElementById("popcorn-loader");

    if (!loader) return;

    const startTime = performance.now();
    const minimumDisplayTime = 1900;
    let hiding = false;

    function hideLoader() {
        if (hiding) return;
        hiding = true;

        const elapsed = performance.now() - startTime;
        const remaining = Math.max(0, minimumDisplayTime - elapsed);

        window.setTimeout(() => {
            loader.classList.add("is-hidden");

            window.setTimeout(() => {
                loader.remove();
            }, 700);

        }, remaining);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", hideLoader, {
            once: true
        });
    } else {
        hideLoader();
    }

    // Fallback in case something delays page loading.
    window.setTimeout(hideLoader, 5000);
})();

// ========================================
// MOOD-BASED FILM DISCOVERY
// ========================================

const moodNames = {
    happy: "Feel-good films",
    heartbroken: "Films for a broken heart",
    romantic: "Stories about love",
    "mind-blown": "Films that challenge your mind",
    melancholic: "Deep and atmospheric cinema",
    motivated: "Films that inspire",
    thrilled: "Edge-of-your-seat cinema",
    adventurous: "Extraordinary adventures"
};

let selectedMood = null;
let moodPage = 1;
let moodTotalPages = 1;
let moodLoading = false;

const moodCards = document.querySelectorAll(".mood-card");
const moodResults = document.getElementById("mood-results");
const moodFilmGrid = document.getElementById("mood-film-grid");
const moodResultsTitle = document.getElementById("mood-results-title");
const moodLoadMore = document.getElementById("mood-load-more");


async function loadMoodMovies(mood, page = 1) {
    if (moodLoading) return;

    moodLoading = true;

    if (page === 1) {
        moodFilmGrid.innerHTML = `
            <p class="loading">Finding films that match your mood...</p>
        `;
    }

    moodLoadMore.disabled = true;

    try {
        const response = await fetch(
            `/movies/mood/${encodeURIComponent(mood)}?page=${page}`
        );

        if (!response.ok) {
            throw new Error("Unable to find mood recommendations.");
        }

        const data = await response.json();

        moodPage = data.page;
        moodTotalPages = data.total_pages;

        const movies = data.movies || [];

        if (page === 1 && !movies.length) {
            moodFilmGrid.innerHTML = `
                <p class="loading">No films found. Try another mood.</p>
            `;
            return;
        }

        const cards = movies.map((movie, index) => {
            const poster = movie.poster_path
                ? `${IMAGE_BASE}w500${movie.poster_path}`
                : null;

            const year = movie.release_date
                ? movie.release_date.substring(0, 4)
                : "N/A";

            const rating = Number(
                movie.vote_average || 0
            ).toFixed(1);

            return `
                <article
                    class="movie-card"
                    data-movie-id="${movie.tmdb_id}"
                    tabindex="0"
                    role="button"
                    aria-label="View ${escapeHTML(movie.title)} details"
                >
                    <div class="frame-number">
                        FRAME ${String((page - 1) * 20 + index + 1).padStart(3, "0")}
                    </div>

                    <div class="poster-wrapper">
                        ${
                            poster
                            ? `
                                <img
                                    src="${poster}"
                                    alt="${escapeHTML(movie.title)}"
                                    loading="lazy"
                                >
                            `
                            : `<div class="poster-placeholder">NO POSTER</div>`
                        }

                        <div class="poster-overlay">
                            <span>★ ${rating}</span>
                            <span class="view-film">VIEW FILM ↗</span>
                        </div>
                    </div>

                    <div class="movie-info">
                        <h3>${escapeHTML(movie.title)}</h3>

                        <div class="movie-meta">
                            <span>${year}</span>
                            <span>★ ${rating}</span>
                        </div>

                        <button class="watchlist-btn" data-watchlist-id="${movie.tmdb_id}" type="button">＋ Watchlist</button>
                    </div>
                </article>
            `;
        }).join("");

        if (page === 1) {
            moodFilmGrid.innerHTML = cards;
        } else {
            moodFilmGrid.insertAdjacentHTML("beforeend", cards);
        }

        moodLoadMore.hidden = moodPage >= moodTotalPages;

    } catch (error) {
        if (page === 1) {
            moodFilmGrid.innerHTML = `
                <p class="error-message">
                    Unable to load recommendations. Please try again.
                </p>
            `;
        }

        console.error(error);

    } finally {
        moodLoading = false;
        moodLoadMore.disabled = false;
    }
}


moodCards.forEach(card => {
    card.addEventListener("click", () => {
        const mood = card.dataset.mood;

        selectedMood = mood;
        moodPage = 1;

        moodCards.forEach(item => {
            item.classList.toggle("selected", item === card);
            item.setAttribute(
                "aria-pressed",
                item === card ? "true" : "false"
            );
        });

        moodResults.hidden = false;

        moodResultsTitle.textContent = moodNames[mood];

        loadMoodMovies(mood, 1);

        moodResults.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    });
});


document.getElementById("clear-mood").addEventListener("click", () => {
    selectedMood = null;
    moodPage = 1;

    moodCards.forEach(card => {
        card.classList.remove("selected");
        card.setAttribute("aria-pressed", "false");
    });

    moodResults.hidden = true;
});


moodLoadMore.addEventListener("click", () => {
    if (!selectedMood || moodPage >= moodTotalPages) return;

    loadMoodMovies(selectedMood, moodPage + 1);
});

document.addEventListener("click", async event => {
    const button = event.target.closest(".watchlist-btn");

    if (!button) return;

    event.preventDefault();
    event.stopPropagation();

    const movieId = button.dataset.watchlistId;

    button.disabled = true;

    try {
        const response = await fetch(`/movies/watchlist/${movieId}`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken()
            }
        });

        const data = await response.json();

        if (response.status === 401) {
            window.location.href = "/auth/login";
            return;
        }

        if (!response.ok) {
            throw new Error(data.error || data.message || "Unable to add movie.");
        }

        button.textContent = "✓ Added";
        button.classList.add("watchlist-added");

    } catch (error) {
        alert(error.message);
        button.disabled = false;
    }
});

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content
        || document.querySelector('input[name="csrf_token"]')?.value
        || "";
}
// ========================================
// PERSONALIZED FOR YOU RECOMMENDATIONS
// ========================================

const forYouGrid = document.getElementById("for-you-grid");
const forYouLoadMore = document.getElementById("for-you-load-more");

let forYouPage = 1;
let forYouTotalPages = 1;
let forYouLoading = false;


async function loadForYouMovies(page = 1) {
    if (!forYouGrid || forYouLoading) return;

    forYouLoading = true;

    if (page === 1) {
        forYouGrid.innerHTML = `
            <p class="loading">Finding films you'll love...</p>
        `;
    }

    if (forYouLoadMore) {
        forYouLoadMore.disabled = true;
    }

    try {
        const response = await fetch(`/movies/for-you?page=${page}`);

        if (response.status === 401) {
            window.location.href = "/auth/login";
            return;
        }

        if (!response.ok) {
            throw new Error("Unable to load personalized recommendations.");
        }

        const data = await response.json();

        forYouPage = data.page;
        forYouTotalPages = data.total_pages;

        const movies = data.movies || [];

        if (page === 1 && movies.length === 0) {
            forYouGrid.innerHTML = `
                <p class="loading">
                    No recommendations available yet.
                    Try adding favorite genres or rating some films!
                </p>
            `;
        } else {
            renderMovies(movies, forYouGrid, page > 1);
        }

        if (forYouLoadMore) {
            forYouLoadMore.hidden =
                movies.length === 0 || forYouPage >= forYouTotalPages;
        }

    } catch (error) {
        if (page === 1) {
            forYouGrid.innerHTML = `
                <p class="error-message">
                    Unable to load your recommendations. Please try again later.
                </p>
            `;
        }

        console.error("For You error:", error);

    } finally {
        forYouLoading = false;

        if (forYouLoadMore) {
            forYouLoadMore.disabled = false;
        }
    }
}


if (forYouGrid) {
    loadForYouMovies();
}

if (forYouLoadMore) {
    forYouLoadMore.addEventListener("click", () => {
        if (forYouPage < forYouTotalPages) {
            loadForYouMovies(forYouPage + 1);
        }
    });
}
