console.log("LocalBird XPostSaver content.js")

const extractPost = () => {
    const article = document.querySelectorAll("article")[0]
    if (!article) return null

    const datatestidElements = [...article.querySelectorAll("[data-testid]")]
    const datatestid2Elements = {}

    for (const e of datatestidElements) {
        const key = e.getAttribute("data-testid")
        if (!datatestid2Elements[key]) {
            datatestid2Elements[key] = []
        }
        datatestid2Elements[key].push(e)
    }

    const authornameElement = datatestid2Elements["User-Name"]?.[0]
    if (!authornameElement) return null

    const author_name = authornameElement.innerText.split("\n")[0]

    let text = ""
    const tweettextElement = datatestid2Elements["tweetText"]?.[0]
    if (tweettextElement) {
        text = tweettextElement.innerText
    }

    const imgs = []
    const tweetPhotos = datatestid2Elements["tweetPhoto"] || []
    for (const e of tweetPhotos) {
        const img = e.querySelector("img")
        if (img) imgs.push(img)
    }
    const image_srcs = imgs.map((e) => e.src)

    const timeElement = article.querySelector("time")
    const created_at = timeElement?.getAttribute("datetime") || ""

    const groups = location.href.match(/https:\/\/x\.com\/(.*)\/status\/(\d+)/)
    const author_id = groups?.[1] || ""
    const id = groups?.[2] || ""

    return {
        image_srcs,
        meta: {
            id,
            author_name,
            author_id,
            text,
            created_at
        },
    }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action == "extractPost") {
        const post = extractPost()
        sendResponse(post)
    }
})
