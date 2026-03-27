async function askQuestion(question, fileId = currentFileId) {
    if (!question || !question.trim()) {
        throw new Error("Please enter a question.");
    }

    if (!fileId) {
        throw new Error("No processed file available for Q&A.");
    }

    const response = await fetch(`http://127.0.0.1:8000/api/qa/${fileId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            question: question.trim(),
        }),
    });

    if (!response.ok) {
        let message = "Failed to get answer.";
        try {
            const errorData = await response.json();
            message = errorData.detail || errorData.message || message;
        } catch (_) {
            // ignore
        }
        throw new Error(message);
    }

    return await response.json();
}

function renderQaAnswer(answerData) {
    const qaAnswer = document.getElementById("qa-answer");
    if (!qaAnswer) return;

    if (!answerData) {
        qaAnswer.textContent = "No answer available.";
        return;
    }

    const answer =
        answerData.answer ||
        answerData.response ||
        (typeof answerData === "string"
            ? answerData
            : JSON.stringify(answerData, null, 2));

    qaAnswer.textContent = answer;
}

function bindQaEvents() {
    const askButton = document.getElementById("ask-question-btn");
    const questionInput = document.getElementById("qa-question");

    if (!askButton || !questionInput) return;

    askButton.addEventListener("click", async () => {
        try {
            askButton.disabled = true;
            askButton.textContent = "Asking...";

            const answerData = await askQuestion(questionInput.value);
            renderQaAnswer(answerData);
        } catch (error) {
            renderQaAnswer(error.message);
        } finally {
            askButton.disabled = false;
            askButton.textContent = "Ask";
        }
    });

    questionInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            askButton.click();
        }
    });
}