window.addEventListener('load', function () {
  const elements = document.getElementsByClassName('updateButton');
  for (let element of elements) {
    element.addEventListener('click', async function () { //asyc function which allows make await returns
      $('#InvisibleProduct').modal('show');
      // await in fetch return which with wait to conclude the request to then return the json obj
      const data = await (await fetch(`/product/${element.id}`)).json()
      // filling form with corresponding item data:
      document.querySelector("#updateForm").setAttribute("action", `/product/${element.id}`);
      nameTxt = document.querySelector("#nameUpdate");

      if (nameTxt.firstChild){
      }
      if (nameTxt.firstChild) {
        nameTxt.removeChild(nameTxt.firstChild)
      }
      nameTxt.appendChild(document.createTextNode(data.name));
      document.querySelector(`#qr_barcodeUpdate${data.qr_barcode}`).setAttribute("selected", 'selected');
      document.querySelector("#descriptionUpdate").setAttribute("value", data.description);
    });
  };
});