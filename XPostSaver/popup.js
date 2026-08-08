/**
 * @returns {HTMLElement}
 */
const $ = (selector) => document.querySelector(selector)
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * @param {HTMLElement} e
 */
const show = (e) => {
    e.removeAttribute("hidden")
}
/**
 * @param {HTMLElement} e
 */
const hide = (e) => {
    e.setAttribute("hidden", true)
}

const $extractedStatus = $("#extracted-status")
const $extractingtatus = $("#extracting-status")
const $jsonPreview = $("#json-preview")
const $downloadButton = $("#download-button")

let currentPostData = null

const downloadJson = () => {
    if (!currentPostData) return
    const filename = currentPostData.meta.id + ".json"
    const content = JSON.stringify(currentPostData, null, 2)
    const blob = new Blob([content], { type: "application/json" })
    const url = URL.createObjectURL(blob)

    chrome.downloads.download({
        url, filename, saveAs: false
    }).then(() => {
        URL.revokeObjectURL(url)
        window.close()
    })
}

const refreshCurrentPostData = async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (tab) {
        chrome.tabs.sendMessage(tab.id, { action: "extractPost" }, response => {
            if (chrome.runtime.lastError || !response) {
                show($extractingtatus)
                hide($extractedStatus)
                return
            }
            currentPostData = response
            $jsonPreview.value = JSON.stringify(response, null, 2)
            show($extractedStatus)
            hide($extractingtatus)
        })
    }
}

const loopRefreshCurrentPostData = async () => {
    while (true) {
        await wait(250)
        refreshCurrentPostData()
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loopRefreshCurrentPostData()
    $downloadButton.addEventListener("click", downloadJson)
    document.addEventListener("keydown", e => {
        if (e.key == "Enter") {
            e.preventDefault()
            downloadJson()
        }
    })
})