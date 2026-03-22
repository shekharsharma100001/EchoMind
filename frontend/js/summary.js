function formatSummary(summary) {
    if (!summary) return "No summary available.";

    if (typeof summary === "string") {
        return summary;
    }

    if (Array.isArray(summary)) {
        return summary.map(item => `• ${item}`).join("\n");
    }

    if (typeof summary === "object") {
        return Object.entries(summary)
            .map(([key, value]) => {
                if (Array.isArray(value)) {
                    return `${key}:\n${value.map(item => `• ${item}`).join("\n")}`;
                }
                return `${key}: ${typeof value === "string" ? value : JSON.stringify(value, null, 2)}`;
            })
            .join("\n\n");
    }

    return String(summary);
}

function renderSummary(summary) {
    const summaryOutput = document.getElementById("summary-output");
    if (!summaryOutput) return;

    summaryOutput.textContent = formatSummary(summary);
}

function formatSentiment(sentiment) {
    if (!sentiment) return "No sentiment report available.";

    if (typeof sentiment === "string") {
        return sentiment;
    }

    if (typeof sentiment === "object") {
        return Object.entries(sentiment)
            .map(([key, value]) => `${key}: ${typeof value === "string" ? value : JSON.stringify(value)}`)
            .join("\n");
    }

    return String(sentiment);
}

function renderSentiment(sentiment) {
    const sentimentOutput = document.getElementById("sentiment-output");
    if (!sentimentOutput) return;

    sentimentOutput.textContent = formatSentiment(sentiment);
}