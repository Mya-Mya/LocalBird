const localbird_saveInStatusPage = () => {
    /* Get Elements */
    let article = document.querySelectorAll("article")[0]
    let datatestidElements = [...article.querySelectorAll("[data-testid]")]
    let datatestid2Elements = {}
    for (let e of datatestidElements) {
        const key = e.getAttribute("data-testid")
        if (key in datatestid2Elements){

        }else{
            datatestid2Elements[key] = []
        }
        datatestid2Elements[key].push(e)
    }

    let usernameElement = datatestid2Elements["User-Name"][0]
    let tweettext = ""
    if (datatestid2Elements["tweetText"] && datatestid2Elements["tweetText"][0]){
        const tweettextElement = datatestid2Elements["tweetText"][0]
        tweettext = tweettextElement.innerText
    }

    let imgs = []
    for(let e of datatestid2Elements["tweetPhoto"]){
        const img = e.querySelector("img")
        imgs.push(img)
    }
    let imgsrcs = imgs.map(e => e.src)

    let datetime = article.querySelector("time").getAttribute("datetime")

    let groups = location.href.match(/https:\/\/x\.com\/(.*)\/status\/(.*)/)
    let userid = groups[1]
    let postid = groups[2]

    /* Make Data */
    let data = {
        username: usernameElement.innerText,
        tweettext,
        datetime,
        imgsrcs,
        userid,
        tweetid: postid
    }
    console.table(data)
    let dataStr = JSON.stringify(data)

    /* Download */
    let filename = `xpostinfo.${userid}.${postid}.json`
    let url = URL.createObjectURL(new Blob([dataStr], { "type": "plain/text" }))
    let a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
}

const localbird_bar = document.createElement("div")
localbird_bar.id = "LocalBirdBar"
localbird_bar.classList.add("LocalBirdUnclicked")
localbird_bar.innerText = "Localbird: Click to Download postinfo JSON"
document.body.insertBefore(localbird_bar, document.body.childNodes[0])

localbird_bar.addEventListener("click",()=>{
    localbird_saveInStatusPage()
    localbird_bar.classList.remove("LocalBirdUnclicked")
    localbird_bar.classList.add("LocalBirdClicked")
    localbird_bar.innerText = "Done"
    window.close()
})