const api_url = "http://localhost:8080";
let current_sidebar_view = "modules";
let current_content_view = "";
let current_db_sidebar_view = "hosts";
let task_update_timeout = null;

function listItemClick(item) {
    listItems = document.getElementById("sidebaritems");
    for (const cur_item of listItems.children) {
        const btn = cur_item.childNodes.item(0);
        if (!btn.isSameNode(item)) {
            btn.className = "sidebaritem inactive";
        } else {
            btn.className = "sidebaritem active";
            current_content_view = btn.innerText;
            console.log(current_content_view);
        }
    }
    renderMainContent();
}

function databaseListItemClick(item) {

}
function databaseTabClick(tab) {
    tabBar = tab.parentElement;
    for (const cur_tab of tabBar.children) {
        if (!cur_tab.isSameNode(tab)) {
            cur_tab.className = "tab inactive";
        } else {
            cur_tab.className = "tab active";
            current_db_sidebar_view = cur_tab.innerHTML.toLowerCase()
        }
    }
    renderDatabaseSideBar();
}

function sidebarTabClick(tab) {
    tabBar = tab.parentElement;
    for (const cur_tab of tabBar.children) {
        if (!cur_tab.isSameNode(tab)) {
            cur_tab.className = "tab inactive";
        }
        else {
            cur_tab.className = "tab active";
            current_sidebar_view = cur_tab.innerText.toLowerCase();
            console.log(current_sidebar_view);
        }
    }
    renderSideBar();
}

function renderSideBar() {
    renderSideBarList(current_sidebar_view);
}

function renderSideBarList(listof) {
    const sidebar = document.getElementById("sidebaritems");
    sidebar.innerHTML = "";
    fetch(api_url + `/${listof}`)
        .then((value) => value.json())
        .then((json) => {
            for (const item of json[listof]) {
                const listitem = document.createElement("li");
                const btn = document.createElement("button");
                btn.innerText = item.name;
                btn.className = "sidebaritem inactive";
                btn.addEventListener("click", () => listItemClick(btn));
                listitem.appendChild(btn);
                sidebar.appendChild(listitem);
            }
        })
        .catch((reason) => {
            console.log(`Cannot render sidebar: ${reason}`)
        })
}

function renderDatabaseSideBar() {
    if (current_db_sidebar_view === "hosts") {
        renderDatabaseSideBarHostsList();
    } else {
        renderDatabaseSideBarCredentialsList();
    }
}

function renderDatabaseSideBarHostsList() {
    const sidebar = document.getElementById("dbpanesidebaritems");
    sidebar.innerHTML = "";
    fetch(api_url + "/hosts")
        .then((res) => res.json())
        .then((json) => {
            for (const host of json.hosts) {
                const listitem = document.createElement("li");
                const btn = document.createElement("button");
                btn.innerText = String(host.id)
                if (host.ipv4) {
                    btn.innerText += ` (${host.ipv4})`;
                } else if (host.ipv6) {
                    btn.innerText += ` (${host.ipv6})`;
                } else if (host.mac) {
                    btn.innerText += ` (${host.mac})`;
                }
                btn.className = "sidebaritem inactive";
                btn.addEventListener("click", () => databaseListItemClick(btn));
                listitem.appendChild(btn);
                sidebar.appendChild(listitem);
            }
            setTimeout(updateDatabaseSideBar, 2000);
        })
}

function updateDatabaseSideBar() {
    const sidebar = document.getElementById("dbpanesidebaritems");
    fetch(api_url + "/hosts")
        .then((res) => res.json())
        .then((json) => {
            let needsupdate = false;
            for (const host of json.hosts) {
                let known = false;
                for (const item of sidebar.children) {
                    if (host.id == item.innerText.split(' ')[0].trim()) {
                        known = true;
                    }
                }
                if (!known) {
                    needsupdate = true;
                    break;   
                }
            }
            if (needsupdate) {
                renderDatabaseSideBar(); 
            }
            setTimeout(updateDatabaseSideBar, 2000);
        })
}

function renderMainContent() {
    if (task_update_timeout !== null) {
        clearTimeout(task_update_timeout);
        task_update_timeout = null;
    }
    switch (current_sidebar_view) {
        case "modules":
            renderModuleInformation();
            break;
        case "tasks":
            renderTaskInformation();
            break;
    }
}

function renderModuleInformation() {
    const main_content = document.getElementById("maincontent");
    fetch(api_url + `/modules/${current_content_view}`)
        .then((value) => value.json())
        .then((module) => {
            const header = document.createElement("h1");
            header.innerText = module.name;
            header.id = "contenttitle";
            const description = document.createElement("p");
            description.innerText = module.description;
            description.id = "contentdescription";
            main_content.innerHTML = "";
            main_content.appendChild(header);
            main_content.appendChild(description);
            const arguments_header = document.createElement("h2");
            arguments_header.innerHTML = "<u>Arguments</u>";
            main_content.appendChild(arguments_header);
            for (const arg of module.args) {
                const argument = document.createElement("div");
                argument.className = "moduleargument";
                const argument_label = document.createElement("layer");
                argument_label.innerHTML = `${arg.name} (<i>${arg.type}</i>): `;
                argument_label.setAttribute("for", arg.name);
                argument.appendChild(argument_label);
                const argument_input = document.createElement("input");
                argument_input.name = arg.name;
                if (arg.type === "bool") {
                    argument_input.type = "checkbox";
                    argument_input.checked = arg.default === 'True';
                } else if (arg.type === "int") {
                    argument_input.type = "number";
                    argument_input.value = arg.default;
                } else {
                    argument_input.type = "text";
                    argument_input.value = arg.default;
                }
                argument.appendChild(argument_input);
                main_content.append(argument);
            }
            main_content.append(document.createElement("br"));
            const start_btn = document.createElement("button");
            start_btn.id = "modulestartbtn";
            start_btn.innerText = "Start";
            start_btn.addEventListener("click", () => runModule());
            main_content.append(start_btn);
        })   
}

function renderTaskInformation() {
    const main_content = document.getElementById("maincontent");
    main_content.innerHTML = "";
    fetch(api_url + `/tasks/${current_content_view}`)
        .then((res) => res.json())
        .then((task) => {
            const header = document.createElement("h1");
            header.innerText = task.name;
            if (!task.running) {
                header.innerText += " (stopped)";
                renderSideBar();
            }
            header.id = "contenttitle";
            main_content.appendChild(header);
            const stop_button = document.createElement("button");
            stop_button.innerText = "Stop Task";
            stop_button.id = "taskstopbutton";
            stop_button.addEventListener("click", () => stopTask());
            main_content.appendChild(stop_button);
            const output_container = document.createElement("pre");
            const output_view = document.createElement("code");
            output_view.innerText = task.full_output;
            output_view.id = "taskoutput";
            output_container.appendChild(output_view);
            main_content.appendChild(output_container);
            if (task.running) {
                task_update_timeout = setTimeout(updateTaskInformation, 500);
            }
        })
}

function updateTaskInformation() {
    fetch(api_url + `/tasks/${current_content_view}`)
        .then((res) => res.json())
        .then((task) => {
            if (!task.running) {
                document.getElementById("contenttitle").innerText += " (stopped)";
                renderSideBar();
            } else {
                if (task.new_output) {
                    document.getElementById("taskoutput").innerText += task.new_output;    
                }
                task_update_timeout = setTimeout(updateTaskInformation, 500);
            }
        })
}
function stopTask() {
    fetch(api_url + `/tasks/${current_content_view}/stop`, {
        method: "post"
    }).then((res) => {
        renderTaskInformation();
    })
}

function runModule() {
    const post_data = new FormData();
    const argument_elements = document.getElementsByClassName("moduleargument");
    for (const arg of argument_elements) {
        const arg_input = arg.children.item(1);
        const arg_name = arg.children.item(0).innerText.split('(')[0].trim();
        let arg_val;
        if (arg_input.type === 'checkbox') {
            arg_val = arg_input.checked;
        } else {
            arg_val = arg_input.value;
        }
        post_data.append(arg_name, String(arg_val));
    }

    fetch(api_url + `/modules/${current_content_view}/start`, {
        method: "POST",
        body: post_data
    }).then((res) => res.text()).then((task_name) => {
        const main_content = document.getElementById("maincontent");
        const new_task = document.createElement("p");
        new_task.innerText = `New task created: ${task_name}`;
        main_content.appendChild(new_task);
    })  
}