const items = document.querySelectorAll(".faq-item");

items.forEach(item => {
    item.addEventListener("click", () => {
        const answer = item.querySelector(".faq-answer");
        const icon = item.querySelector("i");

        items.forEach(i => {
            if (i !== item) {
                i.querySelector(".faq-answer").style.maxHeight = null;
                i.querySelector("i").style.transform = "rotate(0deg)";
            }
        });

        if (answer.style.maxHeight) {
            answer.style.maxHeight = null;
            icon.style.transform = "rotate(0deg)";
        } else {
            answer.style.maxHeight = answer.scrollHeight + "px";
            icon.style.transform = "rotate(180deg)";
        }
    });
});
