document.addEventListener("DOMContentLoaded", () => {
    function getCSRFToken() {
        return document.querySelector(
            'input[name="csrf_token"]'
        )?.value || document.querySelector(
            'meta[name="csrf-token"]'
        )?.content || "";
    }

    async function sendRequest(url, method = "POST") {
        const response = await fetch(url, {
            method,
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }

        return data;
    }

    // Update unread notification count.
    async function updateUnreadCount() {
        const badge = document.getElementById("notification-count");

        try {
            const response = await fetch("/notifications/unread-count");
            if (!response.ok) return;

            const data = await response.json();

            if (badge) {
                badge.textContent = data.count;
                badge.hidden = data.count === 0;
            }
        } catch (error) {
            console.error("Unread count error:", error);
        }
    }

    // Mark one notification as read.
    document.querySelectorAll(".mark-read").forEach(button => {
        button.addEventListener("click", async () => {
            const id = button.dataset.id;

            try {
                await sendRequest(`/notifications/${id}/read`);

                const card = button.closest(".notification-card");

                card.classList.remove("unread");
                button.replaceWith(
                    Object.assign(document.createElement("span"), {
                        className: "read-label",
                        textContent: "Read"
                    })
                );

                updateUnreadCount();
            } catch (error) {
                alert(error.message);
            }
        });
    });

    // Mark all notifications as read.
    const markAllButton = document.getElementById("mark-all-read");

    if (markAllButton) {
        markAllButton.addEventListener("click", async () => {
            try {
                await sendRequest("/notifications/read-all");

                document.querySelectorAll(".notification-card").forEach(card => {
                    card.classList.remove("unread");

                    const button = card.querySelector(".mark-read");

                    if (button) {
                        button.replaceWith(
                            Object.assign(document.createElement("span"), {
                                className: "read-label",
                                textContent: "Read"
                            })
                        );
                    }
                });

                markAllButton.remove();
                updateUnreadCount();
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // Remove a movie from watchlist.
    document.querySelectorAll(".watchlist-remove").forEach(button => {
        button.addEventListener("click", async () => {
            const movieId = button.dataset.id;

            button.disabled = true;

            try {
                await sendRequest(
                    `/movies/watchlist/${movieId}`,
                    "DELETE"
                );

                const card = button.closest(".watchlist-card");
                card.remove();

                if (!document.querySelector(".watchlist-card")) {
                    document.querySelector(".watchlist-grid").innerHTML = `
                        <div class="notifications-empty">
                            <span>✦</span>
                            <h2>Your watchlist is empty</h2>
                            <p>Add movies to keep track of them.</p>
                            <a href="/">Discover movies</a>
                        </div>
                    `;
                }
            } catch (error) {
                alert(error.message);
                button.disabled = false;
            }
        });
    });

    updateUnreadCount();
});