document.addEventListener("DOMContentLoaded", async () => {
    const response = await fetch("/api/logs");
    const logs = await response.json();

    // Helper function to count occurrences
    const countOccurrences = (array, key) => {
        return array.reduce((acc, item) => {
            acc[item[key]] = (acc[item[key]] || 0) + 1;
            return acc;
        }, {});
    };

    // Prepare data for Payloads Chart
    const payloadCounts = countOccurrences(logs, "payload");
    const payloadLabels = Object.keys(payloadCounts);
    const payloadData = Object.values(payloadCounts);

    const payloadsCtx = document.getElementById("payloadsChart").getContext("2d");
    new Chart(payloadsCtx, {
        type: "bar",
        data: {
            labels: payloadLabels,
            datasets: [{
                label: "Payloads Count",
                data: payloadData,
                backgroundColor: "rgba(153, 102, 255, 0.6)",
                borderColor: "rgba(153, 102, 255, 1)",
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Prepare data for Endpoints Chart
    const endpointCounts = countOccurrences(logs, "endpoint");
    const endpointLabels = Object.keys(endpointCounts);
    const endpointData = Object.values(endpointCounts);

    const endpointsCtx = document.getElementById("endpointsChart").getContext("2d");
    new Chart(endpointsCtx, {
        type: "pie",
        data: {
            labels: endpointLabels,
            datasets: [{
                label: "Endpoints Count",
                data: endpointData,
                backgroundColor: ["rgba(255, 99, 132, 0.6)", "rgba(54, 162, 235, 0.6)", "rgba(255, 206, 86, 0.6)"],
                borderWidth: 1
            }]
        },
        options: { responsive: true }
    });

    // Prepare data for IP Addresses Chart
    const ipCounts = countOccurrences(logs, "ip");
    const ipLabels = Object.keys(ipCounts);
    const ipData = Object.values(ipCounts);

    const ipCtx = document.getElementById("ipChart").getContext("2d");
    new Chart(ipCtx, {
        type: "doughnut",
        data: {
            labels: ipLabels,
            datasets: [{
                label: "IP Addresses Count",
                data: ipData,
                backgroundColor: ["rgba(75, 192, 192, 0.6)", "rgba(255, 159, 64, 0.6)", "rgba(153, 102, 255, 0.6)"],
                borderWidth: 1
            }]
        },
        options: { responsive: true }
    });

    // Populate Requests Table
    const tableBody = document.getElementById("requestsTable").querySelector("tbody");
    Object.entries(ipCounts).forEach(([ip, count]) => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${ip}</td><td>${count}</td>`;
        tableBody.appendChild(row);
    });
});
