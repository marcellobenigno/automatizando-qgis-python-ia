// Dashboard dos focos de queimadas na Paraíba (jan.–out. de 2026).
//
// Os dados vêm de três GeoJSON gerados no QGIS pelo script
// modulos/queimadas_pb/queimadas_pb.py: os focos, os municípios e o limite
// do estado. O Vue guarda o estado (filtros, visualização, passo e instante
// da animação); o Leaflet e o Highcharts só desenham.

const { createApp, ref, shallowRef, computed, watch, onMounted, nextTick } = Vue;

const ARQUIVOS = {
  focos: { arquivo: "queimadas_pb_2026.geojson", descricao: "Focos de queimadas" },
  municipios: { arquivo: "municipios_pb.geojson", descricao: "Limites dos municípios" },
  limite: { arquivo: "limite_pb.geojson", descricao: "Limite do estado" },
};
const FUSO = "America/Fortaleza"; // fuso da Paraíba: UTC−3, sem horário de verão
const H3 = 3 * 3600e3;
const DIA = 86400e3;
const ZOOM_CONTORNOS = 9; // a partir daqui, os limites municipais aparecem

const LARANJA = "#eb6834";
const LARANJA_ESCURO = "#9e3812";
const LARANJA_CLARO = "#f7c3a8";
const LARANJA_FORA = "#f39466"; // colunas fora do período mostrado no mapa

// Cada visualização do mapa mostra uma coisa só
const VISUAIS = [
  { valor: "agrupados", rotulo: "Agrupados",
    ajuda: "Os focos próximos viram um círculo com a contagem. Os agrupamentos dependem do zoom: aproxime o mapa para separá-los até cada detecção do satélite." },
  { valor: "densidade", rotulo: "Densidade",
    ajuda: "Onde os focos se concentram. É uma densidade relativa, não uma contagem; a escala é fixa, então um período com menos focos aparece mais claro." },
  { valor: "intensidade", rotulo: "Intensidade (FRP)",
    ajuda: "Cada foco com cor e tamanho pela FRP, a potência radiativa do fogo (MW). A FRP indica a intensidade, não a área queimada." },
  { valor: "municipios", rotulo: "Municípios",
    ajuda: "Focos por município no período mostrado, em 5 classes fixas de contagem. Clique num município para filtrar o painel." },
];
// Agrupamentos: 4 faixas de quantidade
const FAIXAS_CLUSTER = [
  { ate: 10, classe: "faixa-1", lado: 26, cor: "#f39466", rotulo: "1–9" },
  { ate: 50, classe: "faixa-2", lado: 32, cor: "#eb6834", rotulo: "10–49" },
  { ate: 100, classe: "faixa-3", lado: 38, cor: "#c94d1f", rotulo: "50–99" },
  { ate: Infinity, classe: "faixa-4", lado: 44, cor: "#7a1f0b", rotulo: "100 ou mais" },
];
// FRP (MW) em 5 classes: cor e tamanho crescem juntos
const CLASSES_FRP = [
  { ate: 3, cor: "#f39466", raio: 3.5, rotulo: "< 3" },
  { ate: 7, cor: "#eb6834", raio: 4.5, rotulo: "3–7" },
  { ate: 11, cor: "#c94d1f", raio: 5.5, rotulo: "7–11" },
  { ate: 25, cor: "#9e3812", raio: 7, rotulo: "11–25" },
  { ate: Infinity, cor: "#6b2409", raio: 9, rotulo: "≥ 25" },
];
// Coroplético: uma cor só, do claro ao escuro; zero em cinza
const CLASSES_MUNICIPIO = [
  { ate: 1, cor: "#f0efec", rotulo: "0" },
  { ate: 6, cor: "#fbd5c0", rotulo: "1–5" },
  { ate: 21, cor: "#f5a27c", rotulo: "6–20" },
  { ate: 51, cor: "#e0622f", rotulo: "21–50" },
  { ate: Infinity, cor: "#9e3812", rotulo: "mais de 50" },
];
const PASSOS = [
  { valor: "dia", rotulo: "Dia", este: "só este dia" },
  { valor: "semana", rotulo: "Semana", este: "só esta semana" },
  { valor: "mes", rotulo: "Mês", este: "só este mês" },
];

// --------------------------------------------------------------------------
// Datas: tudo em milissegundos UTC; os "passos" começam à meia-noite da PB
// --------------------------------------------------------------------------
const local = (ms) => new Date(ms - H3); // os campos UTC desta data = hora da PB
let INICIO_DO_ANO = 0; // 01/01, 00h na PB: nenhum passo começa antes disso

function inicioDoPasso(ms, passo) {
  const d = local(ms);
  const [a, m, dia] = [d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()];
  let inicio = Date.UTC(a, m, passo === "mes" ? 1 : dia) + H3;
  if (passo === "semana") inicio -= ((d.getUTCDay() + 6) % 7) * DIA; // segunda a domingo
  // a 1ª semana do ano começaria em dezembro: corta em 1º de janeiro
  return Math.max(inicio, INICIO_DO_ANO);
}

function proximoPasso(t, passo) {
  const d = local(t);
  if (passo === "mes") return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1) + H3;
  if (passo === "dia") return inicioDoPasso(t, "dia") + DIA;
  const meiaNoite = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) + H3;
  return meiaNoite + (7 - ((d.getUTCDay() + 6) % 7)) * DIA; // a próxima segunda
}

function listarPassos(inicio, fim, passo) {
  const lista = [];
  for (let t = inicioDoPasso(inicio, passo); t <= fim; t = proximoPasso(t, passo)) lista.push(t);
  return lista;
}

const fmt = (opcoes) => new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, ...opcoes });
const fmtDiaMes = fmt({ day: "2-digit", month: "2-digit" });
const fmtData = fmt({ day: "2-digit", month: "2-digit", year: "numeric" });
const fmtMes = fmt({ month: "long", year: "numeric" });
const fmtDataHora = fmt({ dateStyle: "short", timeStyle: "short" });
const fmtHora = fmt({ hour: "2-digit", hourCycle: "h23" });

function rotuloDoPasso(t, passo) {
  if (passo === "dia") return fmtData.format(t);
  if (passo === "semana") return `${fmtDiaMes.format(t)} a ${fmtData.format(proximoPasso(t, passo) - DIA)}`;
  return fmtMes.format(t);
}

const numero = (n) => n.toLocaleString("pt-BR");
const decimal = (n, casas = 1) =>
  n == null ? "sem dado" : n.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
const classeDe = (classes, valor) => classes.find((c) => valor < c.ate);
const maiuscula = (s) => s.charAt(0).toUpperCase() + s.slice(1);

// --------------------------------------------------------------------------
// Highcharts: português, fuso da PB e um visual discreto para todos
// --------------------------------------------------------------------------
Highcharts.setOptions({
  lang: {
    locale: "pt-BR",
    decimalPoint: ",",
    thousandsSep: ".",
    months: ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
      "agosto", "setembro", "outubro", "novembro", "dezembro"],
    shortMonths: ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    weekdays: ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"],
  },
  time: { timezone: FUSO },
  chart: { style: { fontFamily: "inherit" }, spacing: [8, 4, 14, 0] },
  title: { text: null },
  legend: { enabled: false },
  credits: { position: { y: -2 }, style: { fontSize: "9px" } },
  colors: [LARANJA],
  xAxis: { lineColor: "#c3c2b7", tickColor: "#c3c2b7", labels: { style: { color: "#52514e" } } },
  yAxis: {
    title: { text: null }, gridLineColor: "#e1e0d9",
    labels: { style: { color: "#52514e" } }, allowDecimals: false,
  },
  plotOptions: {
    series: { animation: { duration: 250 }, states: { inactive: { opacity: 1 } } },
    column: { borderRadius: 3, borderWidth: 0 },
    bar: { borderRadius: 3, borderWidth: 0 },
  },
  tooltip: { outside: true },
});

createApp({
  setup() {
    const estado = ref("carregando"); // carregando | pronto | erro
    const erro = ref({ titulo: "", detalhe: "" });
    const arquivos = ref(Object.values(ARQUIVOS).map((a) => ({ ...a, ok: false })));
    const meta = ref({});
    const dados = shallowRef([]); // a lista não muda: não precisa ser profundamente reativa
    const limites = ref({ inicio: 0, fim: 0 });
    const cobertura = ref({ primeiro: 0, ultimo: 0 });

    const municipio = ref("");
    const bioma = ref("");
    const visual = ref("agrupados");
    const passo = ref("mes");
    const modo = ref("janela"); // começa só no passo atual: o acumulado sobrepõe meses
    const tempo = ref(0); // início do passo atual da animação
    const emTelaCheia = ref(false);
    const avisoMapaBase = ref("");

    const mapaEl = ref(null), cartaoMapaEl = ref(null), tempoEl = ref(null), municipioEl = ref(null);
    const municipiosEl = ref(null), periodoEl = ref(null), biomaEl = ref(null), horaEl = ref(null);
    // Objetos do Leaflet e do Highcharts ficam fora do estado reativo do Vue
    let mapa, dimensao, camadas = {}, graficos = {}, limiteEstado, buscaMunicipio;
    const marcadoresCluster = new Map();

    // ---------------- Filtros ----------------
    const janela = computed(() => ({
      inicio: modo.value === "acumulado" ? limites.value.inicio : tempo.value,
      fim: proximoPasso(tempo.value, passo.value),
    }));

    // Cada gráfico de categoria ignora o próprio filtro e destaca a escolha
    function filtrar({ porMunicipio = true, porBioma = true, porTempo = true } = {}) {
      const { inicio, fim } = janela.value;
      return dados.value.filter((f) =>
        (!porMunicipio || !municipio.value || f.municipio === municipio.value) &&
        (!porBioma || !bioma.value || f.bioma === bioma.value) &&
        (!porTempo || (f.t >= inicio && f.t < fim)));
    }

    const base = computed(() => filtrar({ porTempo: false })); // período todo
    const selecao = computed(() => filtrar()); // o que o mapa mostra
    const municipiosComFoco = computed(() =>
      [...new Set(dados.value.map((f) => f.municipio))].sort((a, b) => a.localeCompare(b, "pt-BR")));
    const todosMunicipios = computed(() =>
      [...contar(filtrar({ porMunicipio: false }), (f) => f.municipio)]
        .map(([nome, n]) => ({ nome, n }))
        .sort((a, b) => b.n - a.n || a.nome.localeCompare(b.nome, "pt-BR")));
    const visualAtual = computed(() => VISUAIS.find((v) => v.valor === visual.value));

    const rotuloPasso = computed(() => ({ dia: "dia", semana: "semana", mes: "mês" })[passo.value]);
    // A etiqueta do tempo: o período e se ele é só o passo ou acumulado
    const etiquetaTempo = computed(() => {
      if (estado.value !== "pronto") return "…";
      if (modo.value === "janela") {
        const p = PASSOS.find((x) => x.valor === passo.value);
        const prefixo = { dia: "Dia ", semana: "Semana de ", mes: "" }[passo.value];
        return `${maiuscula(prefixo + rotuloDoPasso(tempo.value, passo.value))} · ${p.este}`;
      }
      const ate = Math.min(janela.value.fim - DIA, limites.value.fim);
      return tempo.value >= inicioDoPasso(limites.value.fim, passo.value)
        ? `Período todo · ${fmtDiaMes.format(limites.value.inicio)} a ${fmtData.format(limites.value.fim)}`
        : `Acumulado de ${fmtDiaMes.format(limites.value.inicio)} a ${fmtData.format(ate)}`;
    });
    const descricaoSelecao = computed(() => {
      const filtros = [municipio.value, bioma.value].filter(Boolean);
      return `${etiquetaTempo.value} · ${filtros.length ? filtros.join(" · ") : "todos os municípios e biomas"}`;
    });

    // ---------------- Indicadores ----------------
    const indicadores = computed(() => {
      if (estado.value !== "pronto") {
        const rotulos = ["Focos", "Municípios atingidos", "Dia com mais focos", "Maior FRP (MW)", "Na Caatinga"];
        return rotulos.map((rotulo) => ({ rotulo, valor: "…", detalhe: "aguardando os dados" }));
      }
      const s = selecao.value;
      const vazio = "sem focos na seleção";
      const [diaPico, nPico] = maior(contar(s, (f) => inicioDoPasso(f.t, "dia")));
      const maxFRP = s.reduce((m, f) => (f.frp > (m?.frp ?? -1) ? f : m), null);
      const caatinga = s.filter((f) => f.bioma === "Caatinga").length;
      return [
        { rotulo: "Focos", valor: numero(s.length), detalhe: "na seleção atual" },
        { rotulo: "Municípios atingidos", valor: numero(new Set(s.map((f) => f.municipio)).size),
          detalhe: "na seleção · de 223 na Paraíba" },
        { rotulo: "Dia com mais focos", valor: s.length ? numero(nPico) : "—",
          detalhe: s.length ? `focos em ${fmtData.format(diaPico)}, na seleção` : vazio },
        { rotulo: "Maior FRP (MW)", valor: maxFRP ? decimal(maxFRP.frp) : "—",
          detalhe: maxFRP ? `${maxFRP.municipio}, ${fmtData.format(maxFRP.t)}` : vazio },
        { rotulo: "Na Caatinga", valor: s.length ? `${Math.round((100 * caatinga) / s.length)}%` : "—",
          detalhe: s.length ? `${numero(caatinga)} de ${numero(s.length)} focos selecionados` : vazio },
      ];
    });

    const maisIntensos = computed(() => [...selecao.value].sort((a, b) => b.frp - a.frp).slice(0, 10));

    function contar(lista, chave) {
      const c = new Map();
      for (const f of lista) c.set(chave(f), (c.get(chave(f)) || 0) + 1);
      return c;
    }
    const maior = (contagem) => [...contagem].reduce((m, par) => (par[1] > m[1] ? par : m), [null, 0]);

    // ---------------- Mapa ----------------
    function criarMapa(municipiosGeo, limiteGeo) {
      mapa = L.map(mapaEl.value, { zoomSnap: 0.25, preferCanvas: true });
      // contornos acima dos dados e sem receber cliques
      mapa.createPane("contornos").style.zIndex = 450;
      mapa.getPane("contornos").style.pointerEvents = "none";

      const bases = {
        "Cinza claro (Esri)": L.tileLayer(
          "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
          { attribution: "Tiles &copy; Esri", maxNativeZoom: 16, maxZoom: 19 }),
        OpenStreetMap: L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 19,
        }),
        "Imagem de satélite (Esri)": L.tileLayer(
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          { attribution: "Tiles &copy; Esri", maxZoom: 18 }),
      };
      // Se o serviço do mapa base falhar, avisa: os dados continuam no mapa
      for (const [nome, camada] of Object.entries(bases)) {
        let falhas = 0;
        camada.on("loading", () => { falhas = 0; });
        camada.on("tileerror", () => {
          if (++falhas === 3) {
            avisoMapaBase.value = `O mapa base "${nome}" não carregou (serviço externo indisponível ou sem internet). ` +
              "Os focos e os controles continuam funcionando; troque o mapa base no ícone de camadas.";
          }
        });
      }
      mapa.on("baselayerchange", () => { avisoMapaBase.value = ""; });
      bases["Cinza claro (Esri)"].addTo(mapa);
      L.control.layers(bases, null, { position: "topright" }).addTo(mapa);
      L.control.scale({ imperial: false, position: "bottomleft" }).addTo(mapa);
      adicionarBotaoInicio();

      // Limites: o estado sempre; os municípios só de perto
      limiteEstado = L.geoJSON(limiteGeo, {
        pane: "contornos", interactive: false,
        style: { color: "#57534e", weight: 1.4, fill: false },
      }).addTo(mapa);
      camadas.contornos = L.geoJSON(municipiosGeo, {
        pane: "contornos", interactive: false,
        style: { color: "#a8a29e", weight: 0.6, fill: false },
      });
      camadas.destaque = L.geoJSON(null, {
        pane: "contornos", interactive: false,
        style: { color: "#1c1917", weight: 2.5, fill: false },
      }).addTo(mapa);

      // Leaflet.markercluster: os focos próximos viram um círculo com a contagem
      camadas.agrupados = L.markerClusterGroup({
        showCoverageOnHover: false,
        maxClusterRadius: 50,
        iconCreateFunction(grupo) {
          const n = grupo.getChildCount();
          const faixa = classeDe(FAIXAS_CLUSTER, n);
          return L.divIcon({ html: n, className: `cluster-foco ${faixa.classe}`, iconSize: [faixa.lado, faixa.lado] });
        },
      });

      // Leaflet.heat: densidade de focos (cada foco pesa 1)
      camadas.densidade = L.heatLayer([], {
        radius: 14, blur: 16, maxZoom: 8, max: 5, minOpacity: 0.2,
        gradient: { 0.25: "#fde68a", 0.5: "#f59e0b", 0.75: "#ea580c", 1: "#7f1d1d" },
      });

      // Intensidade: um círculo por foco, cor e tamanho pela FRP
      camadas.intensidade = L.layerGroup();

      // Coroplético: um polígono por município
      camadas.municipios = L.geoJSON(municipiosGeo, {
        style: () => ({ color: "#ffffff", weight: 0.6, fillOpacity: 0.85 }),
        onEachFeature(feicao, camada) {
          camada.bindTooltip(() => {
            const n = contagemPorMunicipio.get(feicao.properties.municipio) || 0;
            return `<b>${feicao.properties.nome}</b><br>${numero(n)} ${n === 1 ? "foco" : "focos"} · ${etiquetaTempo.value}`;
          }, { sticky: true });
          camada.on("click", () => {
            const nome = feicao.properties.municipio;
            if (!municipiosComFoco.value.includes(nome)) return; // sem focos no ano
            municipio.value = municipio.value === nome ? "" : nome;
          });
        },
      });

      mapa.on("zoomend", mostrarContornos);
      mapa.fitBounds(limiteEstado.getBounds(), { padding: [12, 12] });
    }

    let contagemPorMunicipio = new Map();

    // "Zoom to home": um botão entre o + e o − que volta à Paraíba inteira
    const ICONE_CASA = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/></svg>';

    function voltarAoEstado() {
      mapa.flyToBounds(limiteEstado.getBounds(), { padding: [12, 12], duration: 0.6 });
    }

    function adicionarBotaoInicio() {
      const barra = mapa.zoomControl.getContainer();
      const botao = L.DomUtil.create("a", "controle-inicio");
      botao.href = "#";
      botao.innerHTML = ICONE_CASA;
      botao.title = "Voltar à Paraíba inteira";
      botao.setAttribute("role", "button");
      botao.setAttribute("aria-label", "Voltar ao zoom inicial: a Paraíba inteira");
      barra.insertBefore(botao, barra.querySelector(".leaflet-control-zoom-out"));
      L.DomEvent.on(botao, "click", (e) => {
        L.DomEvent.preventDefault(e);
        voltarAoEstado();
      });
    }

    // Tom Select: o select de municípios vira uma busca que filtra enquanto se digita
    function criarBuscaMunicipio() {
      const focosPor = contar(dados.value, (f) => f.municipio);
      buscaMunicipio = new TomSelect(municipioEl.value, {
        options: municipiosComFoco.value.map((nome) => ({ value: nome, text: nome, n: focosPor.get(nome) })),
        maxOptions: null, // mostra todos, não só os 50 primeiros
        placeholder: "Todos — digite para buscar…",
        plugins: ["clear_button"],
        // ignora acentos e maiúsculas: "sao jose" encontra "SÃO JOSÉ DE PIRANHAS"
        diacritics: true,
        sortField: [{ field: "$score" }, { field: "text" }],
        render: {
          option: (d, esc) => `<div class="option"><span>${esc(d.text)}</span>` +
            `<span class="n" title="focos no ano">${numero(d.n)}</span></div>`,
          no_results: (d, esc) => `<div class="no-results">Nenhum município com focos para "${esc(d.input)}"</div>`,
        },
        onChange: (valor) => { municipio.value = valor || ""; },
      });
    }
    // o filtro também muda por outros caminhos (barras, coroplético, etiquetas)
    watch(municipio, (valor) => {
      if (buscaMunicipio && buscaMunicipio.getValue() !== valor) buscaMunicipio.setValue(valor, true);
    });

    function mostrarContornos() {
      const ver = visual.value !== "municipios" && mapa.getZoom() >= ZOOM_CONTORNOS;
      if (ver) camadas.contornos.addTo(mapa);
      else camadas.contornos.remove();
    }

    function popup(f) {
      const c = classeDe(CLASSES_FRP, f.frp);
      return `
        <p class="text-sm font-semibold text-stone-900">${f.municipio}</p>
        <p class="text-xs text-stone-600">${fmtDataHora.format(f.t)} · ${f.bioma}</p>
        <div class="mt-2 flex items-baseline gap-2 border-t border-stone-100 pt-2">
          <span style="background:${c.cor}" class="inline-block size-2.5 rounded-full"></span>
          <span class="text-xl font-bold text-stone-900">${decimal(f.frp)}</span>
          <span class="text-xs text-stone-600">MW de FRP</span>
        </div>
        <dl class="mt-2 grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs">
          <dt class="text-stone-600">Risco de fogo</dt><dd class="text-right tabular-nums">${decimal(f.risco_fogo, 2)}</dd>
          <dt class="text-stone-600">Dias sem chuva</dt><dd class="text-right tabular-nums">${f.dias_sem_chuva ?? "sem dado"}</dd>
          <dt class="text-stone-600">Precipitação</dt><dd class="text-right tabular-nums">${f.precipitacao == null ? "sem dado" : decimal(f.precipitacao) + " mm"}</dd>
        </dl>`;
    }
    // o recuo mantém o popup longe dos controles do mapa (zoom, camadas)
    const OPCOES_POPUP = { className: "popup-foco", minWidth: 210, maxWidth: 260, autoPanPadding: [60, 60] };

    function marcadorCluster(f) {
      if (!marcadoresCluster.has(f.id)) {
        const m = L.circleMarker([f.lat, f.lon], {
          radius: 5, weight: 1, color: "#ffffff", fillColor: LARANJA, fillOpacity: 0.95,
        }).bindPopup(() => popup(f), OPCOES_POPUP);
        marcadoresCluster.set(f.id, m);
      }
      return marcadoresCluster.get(f.id);
    }

    // Só a camada da visualização atual fica no mapa e é atualizada
    function trocarVisual() {
      for (const nome of ["agrupados", "densidade", "intensidade", "municipios"]) {
        if (nome === visual.value) camadas[nome].addTo(mapa);
        else camadas[nome].remove();
      }
      mostrarContornos();
      atualizarMapa();
    }

    function atualizarMapa() {
      const s = selecao.value;
      if (visual.value === "agrupados") {
        camadas.agrupados.clearLayers();
        camadas.agrupados.addLayers(s.map(marcadorCluster));
      } else if (visual.value === "densidade") {
        camadas.densidade.setLatLngs(s.map((f) => [f.lat, f.lon, 1]));
      } else if (visual.value === "intensidade") {
        camadas.intensidade.clearLayers();
        // os mais intensos por último, para ficarem por cima
        for (const f of [...s].sort((a, b) => a.frp - b.frp)) {
          const c = classeDe(CLASSES_FRP, f.frp);
          L.circleMarker([f.lat, f.lon], {
            radius: c.raio, weight: 0.8, color: "#ffffff", fillColor: c.cor, fillOpacity: 0.9,
          }).bindPopup(() => popup(f), OPCOES_POPUP).addTo(camadas.intensidade);
        }
      } else {
        // no coroplético, o filtro de município só destaca: a contagem ignora esse filtro
        contagemPorMunicipio = contar(filtrar({ porMunicipio: false }), (f) => f.municipio);
        camadas.municipios.setStyle((feicao) => ({
          fillColor: classeDe(CLASSES_MUNICIPIO, contagemPorMunicipio.get(feicao.properties.municipio) || 0).cor,
        }));
      }
    }

    function destacarMunicipio() {
      camadas.destaque.clearLayers();
      if (!municipio.value) {
        voltarAoEstado();
        return;
      }
      camadas.municipios.eachLayer((c) => {
        if (c.feature.properties.municipio === municipio.value) camadas.destaque.addData(c.feature);
      });
      mapa.flyToBounds(camadas.destaque.getBounds(), { padding: [40, 40], maxZoom: 11, duration: 0.6 });
    }

    function mostrarNoMapa(f) {
      if (visual.value !== "agrupados") visual.value = "agrupados";
      nextTick(() => {
        const m = marcadorCluster(f);
        camadas.agrupados.zoomToShowLayer(m, () => m.openPopup());
        cartaoMapaEl.value.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    }

    async function telaCheia() {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await cartaoMapaEl.value.requestFullscreen();
    }
    document.addEventListener("fullscreenchange", () => {
      emTelaCheia.value = Boolean(document.fullscreenElement);
      setTimeout(() => mapa.invalidateSize(), 100);
    });

    // ---------------- Leaflet.TimeDimension ----------------
    // Os instantes são o início de cada passo; a cada "timeload" o Vue
    // recebe o novo instante, e mapa, gráficos e indicadores se atualizam.
    // O controle é criado no mapa e levado para a faixa abaixo dele.
    const ControleTempo = L.Control.TimeDimension.extend({
      _getDisplayDateFormat: (data) => rotuloDoPasso(data.getTime(), passo.value),
    });

    function criarDimensaoTemporal() {
      const instantes = listarPassos(limites.value.inicio, limites.value.fim, passo.value);
      tempo.value = instantes.at(-1);
      dimensao = new L.TimeDimension({ times: instantes, currentTime: tempo.value });
      mapa.timeDimension = dimensao;
      dimensao.on("timeload", (e) => { tempo.value = e.time; });
      const controle = new ControleTempo({
        timeDimension: dimensao,
        loopButton: true,
        timeSliderDragUpdate: true,
        speedSlider: true,
        minSpeed: 0.5, maxSpeed: 6, speedStep: 0.5,
        timeZones: [FUSO],
        playerOptions: { transitionTime: 800, loop: false, startOver: true },
      }).addTo(mapa);
      const caixa = controle.getContainer();
      tempoEl.value.appendChild(caixa);
      // os botões do plugin são <a> sem texto: dá nome a eles para leitores de tela
      const nomes = { "timecontrol-backward": "Passo anterior", "timecontrol-forward": "Próximo passo",
        "timecontrol-play": "Reproduzir ou pausar", "timecontrol-loop": "Repetir ao chegar ao fim" };
      for (const [classe, nome] of Object.entries(nomes)) {
        caixa.querySelector(`.${classe}`)?.setAttribute("aria-label", nome);
      }
    }

    watch(passo, (novo, antigo) => {
      // o instante atual passa a ser o início do passo que o contém;
      // quem estava no último passo continua no último
      const instantes = listarPassos(limites.value.inicio, limites.value.fim, novo);
      const noFim = tempo.value === inicioDoPasso(limites.value.fim, antigo);
      tempo.value = noFim ? instantes.at(-1) : inicioDoPasso(tempo.value, novo);
      dimensao.setAvailableTimes(instantes, "replace");
      dimensao.setCurrentTime(tempo.value);
    });

    // ---------------- Gráficos ----------------
    function criarGraficos() {
      graficos.periodo = Highcharts.chart(periodoEl.value, {
        chart: { type: "column", zooming: { type: "x" } },
        accessibility: { description: "Focos por período; as colunas escuras são o período mostrado no mapa." },
        xAxis: {
          type: "datetime", crosshair: true,
          dateTimeLabelFormats: { day: "%e/%m", week: "%e/%m", month: "%b", year: "%Y" },
        },
        tooltip: {
          formatter() {
            return `<b>${rotuloDoPasso(this.x, passo.value)}</b><br>${numero(this.y)} focos`;
          },
        },
        plotOptions: {
          column: {
            pointPadding: 0.05, groupPadding: 0, borderRadius: 2, cursor: "pointer",
            point: { events: { click() { dimensao.setCurrentTime(this.x); } } },
          },
        },
        series: [{ name: "Focos", data: [] }],
      });

      const barras = (filtro, descricao) => ({
        chart: { type: "bar" },
        accessibility: { description: descricao },
        xAxis: { type: "category", labels: { step: 1, style: { fontSize: "11px", color: "#44403c" } } },
        yAxis: { labels: { enabled: false }, gridLineWidth: 0 },
        tooltip: { pointFormat: "<b>{point.y}</b> focos" },
        plotOptions: {
          bar: {
            pointPadding: 0.08, groupPadding: 0, cursor: "pointer",
            dataLabels: { enabled: true, style: { fontWeight: "600", textOutline: "none", color: "#44403c" } },
            // o clique também vale para Enter/Espaço na navegação por teclado do Highcharts
            point: { events: { click() { filtro.value = filtro.value === this.name ? "" : this.name; } } },
          },
        },
        series: [{ name: "Focos", data: [] }],
      });
      graficos.municipios = Highcharts.chart(municipiosEl.value,
        barras(municipio, "Os 15 municípios com mais focos; ative uma barra para filtrar o painel por esse município."));
      graficos.bioma = Highcharts.chart(biomaEl.value,
        barras(bioma, "Focos por bioma; ative uma barra para filtrar o painel por esse bioma."));

      graficos.hora = Highcharts.chart(horaEl.value, {
        chart: { type: "column" },
        xAxis: { categories: Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, "0")}h`), labels: { step: 3 } },
        tooltip: { pointFormat: "<b>{point.y}</b> focos" },
        plotOptions: { column: { pointPadding: 0.05, groupPadding: 0 } },
        series: [{ name: "Focos", data: [] }],
      });
    }

    function atualizarPeriodo() {
      const contagem = contar(base.value, (f) => inicioDoPasso(f.t, passo.value));
      const { inicio, fim } = janela.value;
      // as colunas do período mostrado no mapa ficam escuras
      const dadosSerie = listarPassos(limites.value.inicio, limites.value.fim, passo.value)
        .map((t) => ({ x: t, y: contagem.get(t) || 0, color: t >= inicio && t < fim ? LARANJA_ESCURO : LARANJA_FORA }));
      const g = graficos.periodo;
      g.series[0].setData(dadosSerie, false);
      g.xAxis[0].removePlotBand("janela");
      g.xAxis[0].addPlotBand({ id: "janela", from: inicio, to: fim, color: "rgba(158,56,18,0.08)", zIndex: 0 });
      g.redraw();
    }

    function atualizarCategorias(grafico, lista, campo, escolhido, limite = Infinity) {
      const pares = [...contar(lista, (f) => f[campo])].sort((a, b) => b[1] - a[1]).slice(0, limite);
      // o escolhido no filtro fica escuro; os demais, claros enquanto houver escolha
      const cor = (nome) => (!escolhido ? LARANJA : nome === escolhido ? LARANJA_ESCURO : LARANJA_CLARO);
      grafico.series[0].setData(pares.map(([nome, y]) => ({ name: nome, y, color: cor(nome) })), true, false, false);
    }

    function atualizarHora() {
      const contagem = contar(base.value, (f) => Number(fmtHora.format(f.t)) % 24);
      graficos.hora.series[0].setData(Array.from({ length: 24 }, (_, h) => contagem.get(h) || 0));
    }

    function atualizarTudo() {
      if (estado.value !== "pronto") return;
      atualizarMapa();
      atualizarCategorias(graficos.municipios, filtrar({ porMunicipio: false }), "municipio", municipio.value, 15);
      atualizarCategorias(graficos.bioma, filtrar({ porBioma: false }), "bioma", bioma.value);
      atualizarPeriodo();
    }

    // ---------------- Ligações ----------------
    watch(selecao, atualizarTudo);
    watch(base, () => { if (estado.value === "pronto") atualizarHora(); });
    watch(visual, trocarVisual);
    watch(municipio, destacarMunicipio);

    // ---------------- Carregamento ----------------
    // Baixa um arquivo e, se falhar, diz qual e por quê
    async function baixar(item) {
      let resposta;
      try {
        resposta = await fetch(item.arquivo);
      } catch {
        const disco = location.protocol === "file:";
        throw new Error(disco
          ? `${item.descricao}: o navegador não lê arquivos com a página aberta direto do disco. ` +
            "Sirva a pasta com python -m http.server ou use o GitHub Pages."
          : `${item.descricao}: sem resposta do servidor (${item.arquivo}). Verifique a conexão.`);
      }
      if (!resposta.ok) {
        throw new Error(`${item.descricao}: o servidor respondeu ${resposta.status} para ${item.arquivo}. ` +
          (resposta.status === 404 ? "O arquivo não foi publicado junto com a página?" : ""));
      }
      try {
        const json = await resposta.json();
        item.ok = true;
        return json;
      } catch {
        throw new Error(`${item.descricao}: ${item.arquivo} não é um GeoJSON válido. Gere-o de novo com o script.`);
      }
    }

    async function carregar() {
      estado.value = "carregando";
      arquivos.value.forEach((a) => { a.ok = false; });
      let focosGeo, municipiosGeo, limiteGeo;
      try {
        [focosGeo, municipiosGeo, limiteGeo] = await Promise.all(arquivos.value.map(baixar));
      } catch (e) {
        erro.value = { titulo: "Os dados do painel não carregaram", detalhe: e.message };
        estado.value = "erro";
        return;
      }
      meta.value = focosGeo.metadados || {};
      dados.value = focosGeo.features.map((f, id) => ({
        id,
        t: Date.parse(f.properties.data_hora),
        lon: f.geometry.coordinates[0],
        lat: f.geometry.coordinates[1],
        ...f.properties,
      }));
      const tempos = dados.value.map((f) => f.t);
      cobertura.value = { primeiro: Math.min(...tempos), ultimo: Math.max(...tempos) };
      INICIO_DO_ANO = Date.UTC(local(cobertura.value.ultimo).getUTCFullYear(), 0, 1) + H3;
      limites.value = { inicio: INICIO_DO_ANO, fim: cobertura.value.ultimo };

      if (!mapa) {
        criarMapa(municipiosGeo, limiteGeo);
        criarGraficos();
        criarDimensaoTemporal();
      }
      estado.value = "pronto";
      await nextTick(); // o select só é habilitado depois que os dados chegam
      if (!buscaMunicipio) criarBuscaMunicipio();
      trocarVisual();
      atualizarTudo();
      atualizarHora();
    }

    onMounted(carregar);

    const botao = (ativo, arredondar = true) =>
      "min-h-9 px-3 py-1.5 text-sm focus-visible:relative focus-visible:z-10 " +
      (arredondar ? "first:rounded-l-md last:rounded-r-md " : "") +
      "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-orange-700 " +
      (ativo ? "bg-orange-700 text-white" : "bg-white text-stone-700 hover:bg-stone-100");
    const etiqueta =
      "inline-flex min-h-9 items-center gap-1.5 rounded-full bg-orange-50 px-3 text-sm font-medium text-orange-900 " +
      "ring-1 ring-orange-200 hover:bg-orange-100 focus-visible:outline-2 focus-visible:outline-orange-700";

    return {
      ARQUIVOS, VISUAIS, PASSOS, FAIXAS_CLUSTER, CLASSES_FRP, CLASSES_MUNICIPIO,
      estado, erro, arquivos, meta, dados, limites, cobertura,
      municipio, bioma, visual, passo, modo, emTelaCheia, avisoMapaBase,
      municipiosComFoco, todosMunicipios, visualAtual, indicadores, maisIntensos,
      rotuloPasso, etiquetaTempo, descricaoSelecao,
      mapaEl, cartaoMapaEl, tempoEl, municipioEl, municipiosEl, periodoEl, biomaEl, horaEl,
      carregar, mostrarNoMapa, telaCheia, botao, etiqueta, numero, decimal,
      formatarData: (t) => fmtData.format(t),
      formatarDataHora: (t) => fmtDataHora.format(t),
    };
  },
}).mount("#app");
