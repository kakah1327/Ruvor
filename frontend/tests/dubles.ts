/**
 * Os dublês de navegador que o jsdom não tem — **o único** lugar deles (o plano do M2.1b, "Os
 * dublês de navegador nos testes"):
 *
 * - `HTMLDialogElement.prototype.showModal` e `close`: abrem e fecham pelo atributo `open`, e o
 *   `close` dispara o evento `close` numa tarefa (`setTimeout`), como o navegador — nunca na
 *   hora. O foco preso dentro do diálogo e o `Esc`
 *   são do navegador, não daqui: provam-se na execução real (T16);
 * - `navigator.clipboard.writeText`: grava o texto em `areaDeTransferencia.textos`, que o teste
 *   lê; com `areaDeTransferencia.falhar`, rejeita, como o navegador que nega a permissão.
 *
 * `instalarDublesDeNavegador()` no `beforeEach` e `restaurarDublesDeNavegador()` no `afterEach`
 * dos testes que abrem diálogo: o que existia antes volta igual, e o que não existia some.
 */

export const areaDeTransferencia: { textos: string[]; falhar: boolean } = {
  textos: [],
  falhar: false,
};

type Saved = {
  showModal: PropertyDescriptor | undefined;
  close: PropertyDescriptor | undefined;
  clipboard: PropertyDescriptor | undefined;
};

let saved: Saved | null = null;

function showModal(this: HTMLDialogElement): void {
  this.setAttribute("open", "");
}

/** Os `close` ainda na fila: o `restaurarDublesDeNavegador()` os descarta. */
const pendingCloses = new Set<ReturnType<typeof setTimeout>>();

function close(this: HTMLDialogElement): void {
  if (!this.hasAttribute("open")) return;
  this.removeAttribute("open");
  // Como o navegador: o atributo sai na hora, e o evento `close` vai **numa tarefa** — a
  // especificação HTML, "close the dialog": "queue an element task on the user interaction task
  // source given the subject element to fire an event named close at subject". Entre um e outro,
  // a tela pode renderizar com o diálogo já fechado e o estado dele ainda aberto.
  const timer = setTimeout(() => {
    pendingCloses.delete(timer);
    this.dispatchEvent(new Event("close"));
  }, 0);
  pendingCloses.add(timer);
}

export function instalarDublesDeNavegador(): void {
  if (saved !== null) restaurarDublesDeNavegador();
  const proto = HTMLDialogElement.prototype;
  saved = {
    showModal: Object.getOwnPropertyDescriptor(proto, "showModal"),
    close: Object.getOwnPropertyDescriptor(proto, "close"),
    clipboard: Object.getOwnPropertyDescriptor(navigator, "clipboard"),
  };
  areaDeTransferencia.textos = [];
  areaDeTransferencia.falhar = false;
  Object.defineProperty(proto, "showModal", {
    configurable: true,
    writable: true,
    value: showModal,
  });
  Object.defineProperty(proto, "close", {
    configurable: true,
    writable: true,
    value: close,
  });
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: {
      writeText: async (text: string): Promise<void> => {
        if (areaDeTransferencia.falhar) {
          throw new DOMException("Write permission denied.", "NotAllowedError");
        }
        areaDeTransferencia.textos.push(text);
      },
    },
  });
}

function put(target: object, key: string, descriptor: PropertyDescriptor | undefined) {
  if (descriptor === undefined) {
    Reflect.deleteProperty(target, key);
  } else {
    Object.defineProperty(target, key, descriptor);
  }
}

export function restaurarDublesDeNavegador(): void {
  if (saved === null) return;
  for (const timer of pendingCloses) clearTimeout(timer);
  pendingCloses.clear();
  put(HTMLDialogElement.prototype, "showModal", saved.showModal);
  put(HTMLDialogElement.prototype, "close", saved.close);
  put(navigator, "clipboard", saved.clipboard);
  saved = null;
}
