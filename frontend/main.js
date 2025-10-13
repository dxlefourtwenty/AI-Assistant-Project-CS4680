document.getElementById("storyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const loading = document.getElementById("loading");
  const output = document.getElementById("output");
  output.innerHTML = "";
  loading.classList.remove("hidden");

  const payload = {
    experience_level: document.getElementById("experience_level").value,
    genre: document.getElementById("genre").value,
    characters: document.getElementById("characters").value,
    interests: document.getElementById("interests").value,
    user_brainstorm: document.getElementById("user_brainstorm").value,
  };

  try {
    const res = await fetch("http://127.0.0.1:8000/api/story", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    loading.classList.add("hidden");

    if (data.stories && Array.isArray(data.stories)) {
      data.stories.forEach((story) => {
        const card = document.createElement("div");
        card.className =
          "bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-lg transition-all hover:shadow-indigo-700/30";

        card.innerHTML = `
          <h2 class="text-2xl font-bold text-indigo-400 mb-2">${story.title}</h2>
          <p class="text-sm text-gray-400 mb-3 italic">${story.genre_subgenre}</p>
          <p class="mb-4">${story.premise}</p>

          <div class="mb-4">
            <h3 class="font-semibold text-indigo-300 mb-1">Main Characters</h3>
            <ul class="list-disc list-inside text-sm space-y-1">
              ${story.main_characters
                .map(
                  (ch) =>
                    `<li><strong>${ch.name}</strong> — ${ch.role}, ${ch.personality}, motivated by ${ch.motivation}</li>`
                )
                .join("")}
            </ul>
          </div>

          <p><strong>Central Conflict:</strong> ${story.central_conflict}</p>
          <p><strong>Themes:</strong> ${story.themes.join(", ")}</p>
          <p><strong>Tone & Style:</strong> ${story.tone_and_style}</p>
          <p class="mt-2 text-gray-400 text-sm"><strong>Why it works for you:</strong> ${story.why_it_works_for_this_writer}</p>
        `;

        // Animate fade-in
        card.style.opacity = "0";
        output.appendChild(card);
        setTimeout(() => (card.style.transition = "opacity 0.6s ease"), 0);
        setTimeout(() => (card.style.opacity = "1"), 50);
      });
    } else {
      output.innerHTML = `<p class="text-red-400 text-center">Error: Invalid response format.</p>`;
    }
  } catch (err) {
    loading.classList.add("hidden");
    output.innerHTML = `<p class="text-red-400 text-center">Error connecting to API.</p>`;
    console.error(err);
  }
});
