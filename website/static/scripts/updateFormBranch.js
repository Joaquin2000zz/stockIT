window.addEventListener('load', function() {
    const elements = document.getElementsByClassName('updateButton');
    for (let element of elements) {
      element.addEventListener('click', async function () { //asyc function which allows make await returns
        $('#InvisibleBranch').modal('show');
        // await in fetch return which with wait to conclude the request to then return the json obj
        const data = await (await fetch(`/branch/${element.id}`)).json()
        // filling form with corresponding branch data:
        document.querySelector("#updateForm").setAttribute("action", `/branch/${element.id}`);
        document.querySelector("#nameUpdate").setAttribute("value", data.name);
     
      });
    };
  });