const wait = (time) => new Promise((resolve) => setTimeout(resolve, time))

/* 投稿情報を抽出する */
const extractPostInfo = () => {
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

    const usernameElement = datatestid2Elements["User-Name"]?.[0]
    if (!usernameElement) return null

    const username = usernameElement.innerText.split("\n")[0]

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
    const imgsrcs = imgs.map((e) => e.src)

    const timeElement = article.querySelector("time")
    const datetime = timeElement?.getAttribute("datetime") || ""

    const groups = location.href.match(/https:\/\/x\.com\/(.*)\/status\/(\d+)/)
    const userid = groups?.[1] || ""
    const postid = groups?.[2] || ""

    return {
        username,
        text,
        datetime,
        imgsrcs,
        userid,
        postid,
    }
}

/* JSONファイル名を作る */
const makeJsonFilename = ({ userid, postid }) => {
    return `xpostinfo.${userid}.${postid}.json`
}

/* JSON文字列を作る */
const makeJsonString = (data) => {
    return JSON.stringify(data, null, 2)
}

/* JSONファイルを作成してダウンロードする */
const downloadJsonFile = (filename, dataStr) => {
    const url = URL.createObjectURL(
        new Blob([dataStr], { type: "application/json" })
    )

    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    a.remove()

    URL.revokeObjectURL(url)
}

/* UIを作る */
const createLocalbirdBar = () => {
    const bar = document.createElement("div")
    bar.id = "LocalBirdBar"
    // bar.style.display = "box"
    bar.style.flexDirection = "column"
    bar.style.gap = "4px"
    bar.style.padding = "4px"
    bar.style.background = "white"

    const button = document.createElement("button")
    button.type = "button"
    button.textContent = "Download postinfo JSON"
    button.style.width = "100%"
    button.style.height = "70px"
    button.style.background = "black"
    button.style.color = "white"

    const textarea = document.createElement("textarea")
    textarea.id = "LocalBirdJsonPreview"
    textarea.rows = 10
    textarea.readOnly = true
    textarea.style.width = "100%"
    textarea.style.boxSizing = "border-box"
    textarea.style.background = "gray"
    textarea.style.color = "white"

    bar.appendChild(button)
    bar.appendChild(textarea)

    return { bar, button, textarea }
}

/* UIが正しくページに載るまで、UI追加を繰り返す */
const installLocalbirdBarUntilSuccess = async () => {
    for (let i = 0; i < 100; i++) {
        await wait(100)

        if (document.getElementById("LocalBirdBar")) break

        try {
            const section = document.querySelectorAll("section")[0]
            if (!section || !section.parentElement) continue

            const { bar, button, textarea } = createLocalbirdBar()
            section.parentElement.insertBefore(bar, section)

            button.addEventListener("click", () => {
                const data = extractPostInfo()
                if (!data) return

                const filename = makeJsonFilename(data)
                const dataStr = makeJsonString(data)
                downloadJsonFile(filename, dataStr)
            })

            startTextareaSync(textarea)
            break
        } catch (error) {
            // 失敗したら次のループで再試行
        }
    }
}

/* textareaへJSON内容を1秒ごとに同期する */
const startTextareaSync = (textarea) => {
    console.log(".")
    let lastText = ""

    const sync = () => {
        const data = extractPostInfo()
        if (!data) return

        const currentText = makeJsonString(data)
        if (currentText === lastText) return

        lastText = currentText
        textarea.value = currentText
    }
    sync()
    setInterval(sync, 1000)
}

/* URLが変わったらLocalbirdBarの設置試行を行なう */
const startUrlChangeObservation = () => {
    let lastUrl = location.href
    const observeUrlChange = () => {
        const currentUrl = location.href

        if (currentUrl !== lastUrl) {
            lastUrl = currentUrl
            installLocalbirdBarUntilSuccess()
        }
    }
    setInterval(observeUrlChange, 500)
}

// Startup
installLocalbirdBarUntilSuccess()
startUrlChangeObservation()
