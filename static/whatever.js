function validateForm(event) {
    event.preventDefault();
    const player = document.getElementById("player");
    const team = document.getElementById("team");
    const time = document.getElementById("time");
    const pattern = /^\d{1,2}:[0-5]\d\.\d$/;
    if (time.value.trim() !== "" && !pattern.test(time.value)) {
        time.style.border = '3px solid red';
        return;
    }    
    const season = document.getElementById("season");
    let inputdata = [player, team, time, season];
    for (const data of inputdata) {
        if (!checkData(data)) {
            return;
        }
    }
    if (!checkRadioGroups()) {
        return;
    }
    let writtendata = {
        "player" : player.value,
        "team" : team.value,
        "time" : time.value,
        "season" : season.value
    }
    let checkeddata = getSelectedOptions();
    let alldata = {...writtendata, ...checkeddata}
    getChart(alldata);
}

function checkRadioGroups() {
    const groups = ['location', 'shottype', 'shotmade'];
    for (let name of groups) {
        const checked = document.querySelector("input[name='" + name + "']:checked");
        if (!checked) {
            document.querySelector("." + name).style.color = 'red';
            return false;
        } else {
            document.querySelector("." + name).style.color = 'white';
        }  
    }
    return true;
}

function checkData(data) {
    if (data.value.trim() === '') {
        data.style.border = '3px solid red';
        return false;
    } else {
        data.style.border = '1px solid grey';
        return true;
    }
}

function getSelectedOptions() {
    const location = document.querySelector("input[name='location']:checked").value;
    const shottype = document.querySelector("input[name='shottype']:checked").value;
    const shotmade = document.querySelector("input[name='shotmade']:checked").value;
    const data = {
        "location" : location,
        "shottype" : shottype,
        "shotmade" : shotmade
    };
    return data;
}

function getChart(alldata) {
    fetch('/query', {
        method : 'POST',
        headers : {
            'Content-Type' : 'application/json'
        },
        body : JSON.stringify(alldata)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Error') {
            document.querySelector(".message").innerHTML = 'An Error Occurred. Please ensure you entered valid data';
        } else if (data.message === 'Success') {
            const chart = document.querySelector("input[name='charttype']:checked").value;
            if (chart.trim() == 'scatter') {
                showScatter();
            } else {
                showHeatMap();
            }
        }
    })
}

function showHeatMap() {
    fetch('/get_heatmap')
    .then(async (resp) => {
        if (resp.status !== 200) {
            throw new Error(await resp.text());
        } else {
            return resp.blob();
        }
    })
    .then((blob) => {
        let img = URL.createObjectURL(blob);
        document.getElementById("chart").setAttribute('src', img);
    })
}

function showScatter() {
    fetch('/get_scatter')
    .then(async (resp) => {
        if (resp.status !== 200) {
            throw new Error(await resp.text());
        } else {
            return resp.blob();
        }
    })
    .then((blob) => {
        let img = URL.createObjectURL(blob);
        document.getElementById("chart").setAttribute('src', img);
    })
}