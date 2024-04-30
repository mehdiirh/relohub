function hasTime(endDatetime) {
    let endDate = new Date(endDatetime)
    let now = new Date()
    let remained = endDate - now
    return remained > 0
}

function formatTimer(endDatetime, startDatetime=null) {
    let endDate = new Date(endDatetime)
    let now = new Date()
    let remained = endDate - now
    remained = parseInt(remained / 1000)

    let minutes = parseInt(remained / 60)
    let seconds = remained - minutes * 60

    minutes = Math.abs(minutes).toString()
    seconds = Math.abs(seconds).toString()

    if (minutes.length === 1)
        minutes = "0" + minutes

    if (seconds.length === 1)
        seconds = "0" + seconds

    let time = `${minutes}:${seconds}`

    if (remained < 0)
        time = "-" + time

    let passedTimePercent = 0;
    if (startDatetime) {
        let startDate = new Date(startDatetime)
        let passedTime = now - startDate
        let totalTime = endDate - startDate

        passedTimePercent = (passedTime / totalTime) * 100
    }

    return [time, passedTimePercent];

}


function countDown(timer, loader, endDatetime, startDatetime =null) {
    const timerObject = document.querySelector(timer)
    const loaderObject = document.querySelector(loader)

    let interval = setInterval(
        () => {
            let [remainedTime, passedTimePercent] = formatTimer(endDatetime, startDatetime)

            if (passedTimePercent >= 50 && passedTimePercent < 80) {
                timerObject.classList.replace("info", "warning")
                loaderObject.classList.replace("info", "warning")
            }
            else if (passedTimePercent >= 80) {
                timerObject.classList.replace("info", "error")
                timerObject.classList.replace("warning", "error")
                loaderObject.classList.replace("info", "error")
                loaderObject.classList.replace("warning", "error")
            }

            if (hasTime(endDatetime)) {
                timerObject.textContent = remainedTime
            } else {
                timerObject.textContent = "00:00"
                clearInterval(interval)
                window.location.reload();
            }

        },
        1000
    )

}
