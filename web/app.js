const currency = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 });
let products = [];
let toastTimer;

const $ = (selector) => document.querySelector(selector);

function showToast(message, error = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3300);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la solicitud.");
  return data;
}

function renderProducts() {
  const body = $("#product-rows");
  const empty = $("#empty-inventory");
  body.replaceChildren();
  empty.hidden = products.length > 0;
  $("#table-count").textContent = `${products.length} ${products.length === 1 ? "referencia" : "referencias"}`;
  $("#stat-products").textContent = products.length;
  $("#stat-stock").textContent = number.format(products.reduce((sum, item) => sum + item.stock_m3, 0));
  $("#stat-types").textContent = new Set(products.map((item) => item.tipo)).size;

  products.forEach((item) => {
    const row = document.createElement("tr");
    const typeName = item.tipo === "arena" ? "Arena" : "Grava";
    const stockClass = item.stock_m3 < 10 ? "stock-pill low" : "stock-pill";
    row.innerHTML = `<td><div class="material-cell"><span class="material-thumb ${item.tipo}">${item.tipo === "arena" ? "&#9670;" : "&#9632;"}</span><span><span class="material-name"></span><span class="material-type">${typeName}</span></span></div></td><td class="origin-cell"></td><td class="money-cell">${currency.format(item.precio_m3)}</td><td><span class="${stockClass}">${number.format(item.stock_m3)} m&sup3;</span></td><td><span class="type-pill">Disponible</span></td>`;
    row.querySelector(".material-name").textContent = item.nombre;
    row.querySelector(".origin-cell").textContent = item.origen;
    body.append(row);
  });

  const select = $("#quote-product");
  const selected = select.value;
  select.replaceChildren(new Option("Selecciona material", ""));
  products.forEach((item) => select.add(new Option(`${item.nombre} - ${typeNameLabel(item.tipo)} (${number.format(item.stock_m3)} m3)`, item.id)));
  if (products.some((item) => String(item.id) === selected)) select.value = selected;
}

function typeNameLabel(tipo) { return tipo === "arena" ? "Arena" : "Grava"; }

async function loadProducts() {
  try {
    products = await request("/api/products");
    renderProducts();
  } catch (error) {
    showToast(error.message, true);
  }
}

function openDialog() {
  $("#product-form").reset();
  $("#product-dialog").showModal();
}

$("#open-product").addEventListener("click", openDialog);
$("#empty-add").addEventListener("click", openDialog);
$("#close-dialog").addEventListener("click", () => $("#product-dialog").close());
$("#cancel-dialog").addEventListener("click", () => $("#product-dialog").close());

$("#product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  const payload = {
    tipo: $("#product-type").value,
    nombre: $("#product-name").value.trim(),
    precio_m3: Number($("#product-price").value),
    stock_m3: Number($("#product-stock").value),
    origen: $("#product-origin").value.trim(),
  };
  try {
    const product = await request("/api/products", { method: "POST", body: JSON.stringify(payload) });
    products.push(product);
    renderProducts();
    $("#product-dialog").close();
    showToast(`${product.nombre} se agregó al inventario.`);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("#quote-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  const payload = {
    producto_id: Number($("#quote-product").value),
    cantidad_m3: Number($("#quote-quantity").value),
    distancia_km: Number($("#quote-distance").value),
  };
  try {
    const result = await request("/api/quote", { method: "POST", body: JSON.stringify(payload) });
    $("#result-material-label").textContent = `${number.format(result.cantidad_m3)} m3 de ${result.producto}`;
    $("#result-material").textContent = currency.format(result.material);
    $("#result-freight").textContent = currency.format(result.flete);
    $("#result-total").textContent = currency.format(result.total);
    $("#quote-result").hidden = false;
  } catch (error) {
    showToast(error.message, true);
    $("#quote-result").hidden = true;
  } finally {
    button.disabled = false;
  }
});

loadProducts();
