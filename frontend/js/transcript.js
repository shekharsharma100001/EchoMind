function renderTranscript(transcript) {
    const resultsSection = document.getElementById("results-section");
    const transcriptOutput = document.getElementById("transcript-output");

    if (resultsSection) {
        resultsSection.classList.remove("hidden");
    }

    if (!transcriptOutput) return;

    if (!transcript) {
        transcriptOutput.textContent = "No transcript available.";
        return;
    }

    if (typeof transcript === "string") {
        transcriptOutput.textContent = transcript;
        return;
    }

    transcriptOutput.textContent = JSON.stringify(transcript, null, 2);
}


function renderConversation(conversation) {
    const conversationOutput = document.getElementById("conversation-output");
    if (!conversationOutput) return;

    if (!conversation) {
        conversationOutput.textContent = "No diarized transcript available.";
        return;
    }

    conversationOutput.textContent = conversation;
}