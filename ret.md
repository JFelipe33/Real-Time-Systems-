# RET — Timing Evidence Report

**Team:** Juan Felipe Pachon Restrepo · **Boards:** Aun por decidir (ESP 32 C6 O S3) · **Living** document: updated
every week; handed in at the workshop (week 8) and at the close (week 16).
House rule: *"show me the trace"* — every timing claim cites a measurement.

## 1. The system and its task set

Requirements first — one sentence each, EARS style (*when/while <condition>, the
system shall <response> within <deadline>*) — then the task that implements them:

| ID | Requirement |
|---|---|
| REQ-CTRL-01 | While the system is irrigating, the control loop shall run every 10 ms (deadline = period). |
| REQ-CTRL-02 | When pressure exceeds the overpressure threshold, the system shall close the valve within 5 ms. |
| REQ-SAMP-01 | While the system is operating, the sampling task shall execute every 1 ms with jitter bounded within <X> µs. |
| REQ-CONS-01 | When a console command is received, the system shall respond within <Y> ms or discard it as stale. |
| REQ-TEL-01 | While the system is irrigating, the telemetry task shall transmit a CSV line every 1000 ms. |
| REQ-FLOW-01 | While flow pulses accumulate, the system shall compute the flow batch every 100 pulses without blocking the sampling task. |

| Task | Req. | Type (H/F/S) | Period | Deadline | Measured C_i | How it was measured |
|---|---|---|---|---|---|---|
| Control loop | REQ-CTRL-01 | Hard | 10 ms | = T | ____ | <GPIO + analyzer / trace> |
| Overpressure e-stop | REQ-CTRL-02 | Hard | aperiodic | 5 ms | ____ | <GPIO + analyzer / trace> |
| Sampling | REQ-SAMP-01 | Hard | 1 ms | = T | ____ | <GPIO + analyzer / trace> |
| Console | REQ-CONS-01 | Firm | aperiodic | ____ | ____ | <GPIO + analyzer / trace> |
| Telemetry | REQ-TEL-01 | Soft | 1000 ms | = T | ____ | <GPIO + analyzer / trace> |
| Flow batch | REQ-FLOW-01 | — | ~100 ms | ____ | ____ | <GPIO + analyzer / trace> |

## 2. ADRs

### ADR-001 — <title>
**Context:** … · **Decision:** … · **Justification (with numbers):** … · **Status:** …

## 3. Evidence by week

### Week 2 — superloop baseline (C0116-DK)

#### Diagrama de flujo (Task A)

```mermaid
flowchart TD
    subgraph ISR["ISR Flags"]
        direction TB
        isr_info["• <b>Timer ISR:</b> incrementa <code>ticks_pending</code> cada 1 ms<br/>• <b>Flow ISR:</b> incrementa <code>flow_pulses</code> por cada pulso"]
    end

    init["<b>Inicialización</b><br/><code>init_hw()</code> configura GPIOs, ADC e interrupción de flujo.<br/>Se inicia el timer de 1 ms y comienza el <code>while(1)</code>."]
    
    polled["<b>Polled work</b><br/><code>task_console()</code>: <code>instr_cons</code> = 1 al procesar → 0 al terminar<br/><code>task_display()</code>: <code>instr_disp</code> = 1 al redibujar → 0 al terminar<br/><code>task_telemetry()</code>: <code>instr_tele</code> = 1 al transmitir → 0 al terminar"]
    
    tick{"¿<code>ticks_pending</code> > 0?"}
    
    sample["<b>Sampling / Control</b><br/>Se consume 1 tick → <code>task_sampling()</code><br/><code>instr_samp</code>: 1 al entrar → 0 al salir<br/>Cada 10 muestras → <code>task_control()</code><br/><code>instr_ctrl</code>: 1 al entrar → 0 al salir"]
    
    flow["<b>Polled work: Flow</b><br/><code>task_flow_batch()</code> comprueba: <code>flow_pulses >= 100</code><br/>Si cumple: <code>instr_flow</code> = 1 al entrar → 0 al terminar el cálculo"]

    ISR --> init
    init --> polled
    polled --> tick
    tick -- Sí --> sample
    tick -- No --> flow
    sample --> flow
    flow --> polled
```

#### Resumen de mediciones del superloop

| Medición | Mi valor | Referencia |
| :--- | :---: | :--- |
| **Período real de muestreo (nominal 1 kHz): promedio** | $996.03\ \mu\text{s}$ | $1000\ \mu\text{s}$ |
| **Jitter de muestreo: máximo durante $\ge 30$ s** | $22578\ \mu\text{s}$ | Registrar el valor obtenido; es la referencia del curso |
| **Latencia ISR $\rightarrow$ atención del superloop (pulso de flujo)** | $14.5\ \mu\text{s}$ | Valor medido en el analizador lógico |
| **Jitter de muestreo máximo con la caché de Flash desactivada** | $24239\ \mu\text{s}$ | La diferencia respecto al jitter base corresponde al acelerador ART |
| **Jitter de muestreo con el comando bloqueante activo** | $437588\ \mu\text{s}$ | Comparar con el jitter base |
| **`backlog_peak`, en reposo $\rightarrow$ durante el comando bloqueante** | $30 \rightarrow 440$ ticks | Misma situación, medida por el firmware |

* **Fórmulas usadas:**
  * Jitter máximo = Max − nominal ($1000\ \mu\text{s}$)
  * Latencia ISR = $\Delta t$ entre flancos de CH0 y CH4 (marcador de tiempo)
  * Consistencia firmware/analizador $\approx$ `backlog_peak` $\times 1\text{ ms}$

---

#### Captura base: cache ON (Task B)

<img width="1600" height="850" alt="logic1" src="https://github.com/user-attachments/assets/f6b55365-2ad4-47e9-89ff-0390e9fe7083" />
<img width="1600" height="850" alt="logic2" src="https://github.com/user-attachments/assets/05bd9e11-39a0-439b-b4e7-e639f78e2170" />

##### Estadísticas de periodo del canal CH0 (`instr_samp`), captura de 30 s

| Parámetro | Valor | Parámetro | Valor |
| :--- | :--- | :--- | :--- |
| $\Delta T$ | $30.087168\text{ s}$ | $N_{\text{falling}}$ | $30198$ |
| $N_{\text{rising}}$ | $30198$ | $f_{\text{min}}$ | $42.413\text{ Hz}$ |
| $f_{\text{max}}$ | $61776.062\text{ Hz}$ | $f_{\text{mean}}$ | $1003.981\text{ Hz}$ |
| $T_{\text{std}}$ | $1.0454\text{ ms}$ | Min | $16.19\ \mu\text{s}$ |
| **Mean** | **$996.03\ \mu\text{s}$** | Freq | $1003.981\text{ Hz}$ |
| SDev | $1045.42\ \mu\text{s}$ | **Max** | **$23577.75\ \mu\text{s}$** |
| Count | $30197$ | | |

<img width="1600" height="850" alt="logic4" src="https://github.com/user-attachments/assets/8659115a-4b3f-4c05-ae9e-d697fdeb1cd2" />
*Figura 2: Marcador de tiempo entre CH0 y CH4: $\Delta t = 14.5\ \mu\text{s}$ (latencia ISR $\rightarrow$ atención del superloop).*

---

#### Rebuild cache OFF (Task B)

<img width="1600" height="950" alt="logic5" src="https://github.com/user-attachments/assets/113af4f2-b065-4bda-8b37-c9d1fafc29c8" />
<img width="1600" height="950" alt="logic6" src="https://github.com/user-attachments/assets/abf8d943-f690-4099-8494-55bc11ffcbd3" />

##### Estadísticas de periodo del canal CH0 (`instr_samp`), captura de 30 s, caché desactivada

| Parámetro | Valor | Parámetro | Valor |
| :--- | :--- | :--- | :--- |
| $\Delta T$ | $30.108416\text{ s}$ | $N_{\text{falling}}$ | $30220$ |
| $N_{\text{rising}}$ | $30220$ | $f_{\text{min}}$ | $39.621\text{ Hz}$ |
| $f_{\text{max}}$ | $42553.191\text{ Hz}$ | $f_{\text{mean}}$ | $1003.706\text{ Hz}$ |
| $T_{\text{std}}$ | $1.1157\text{ ms}$ | Min | $23.50\ \mu\text{s}$ |
| **Mean** | **$996.31\ \mu\text{s}$** | Freq | $1003.706\text{ Hz}$ |
| SDev | $1115.66\ \mu\text{s}$ | **Max** | **$25239.44\ \mu\text{s}$** |
| Count | $30219$ | | |

---

#### calib activo (Task C)

<img width="1600" height="950" alt="logic7" src="https://github.com/user-attachments/assets/55df2670-c7d8-451a-96c7-6f80ee65e436" />
*Figura 4: Captura del analizador lógico durante el disparo de `calib`, CH0 (`instr_samp`).*

```text
t=23000 ... backlog=30
calib
calibrating zero-flow offset (1000 rounds)...
calibration done
t=25000 ... backlog=440
...
status
p=1489 mV sp=1500 mV duty=45% flow_x100=0 estop=0
batches=0 backlog_peak=440
```

##### Estadísticas de periodo del canal CH0 (`instr_samp`), captura con `calib` activo

| Parámetro | Valor | Parámetro | Valor |
| :--- | :--- | :--- | :--- |
| $\Delta T$ | $20.015616\text{ s}$ | $N_{\text{falling}}$ | $20088$ |
| $N_{\text{rising}}$ | $20088$ | $f_{\text{min}}$ | $2.280\text{ Hz}$ |
| $f_{\text{max}}$ | $42553.191\text{ Hz}$ | $f_{\text{mean}}$ | $1003.635\text{ Hz}$ |
| $T_{\text{std}}$ | $3.2828\text{ ms}$ | Min | $23.50\ \mu\text{s}$ |
| **Mean** | **$996.38\ \mu\text{s}$** | Freq | $1003.635\text{ Hz}$ |
| SDev | $3282.80\ \mu\text{s}$ | **Max** | **$438588.31\ \mu\text{s}$** |
| Count | $20087$ | | |

La tarea que sufre es `task_sampling()` (y por extensión `task_control()`, que depende de ella): mientras `cmd_calib()` ejecuta sus 1000 rondas de `k_busy_wait(400)` dentro de `task_console()` (`main.c`, función `cmd_calib`), el `while(1)` del superloop no vuelve a pasar por el bloque que drena `ticks_pending`, así que los 1 kHz ticks generados por `tick_isr()` se acumulan sin ser atendidos. La causa raíz no es la interrupción, sino que el superloop no tiene forma de interrumpir una tarea polled a media ejecución: `calib` es bloqueante y monopoliza el único hilo de ejecución hasta terminar sus 1000 rondas ($\approx 400\ \mu\text{s} \times 1000 \approx 400\text{ ms}$ sólo en `k_busy_wait`, que coincide con los $\approx 437\text{ ms}$ medidos).

---

### Week 3 — S3 baseline and silicon comparison
…

## 4. Schedulability analysis

U = ΣC_i/T_i with **measured** C_i; test used (RM / hyperbolic / EDF); RTA as a
script with its output; blocking B_i if there are mutexes. (Formulas: READINGS.md,
"The math that does get used".)

## 5. Functional safety (final project)

Declared safe state (failure ⇒ valve closed), watchdog, and the evidence of the
fail-safe firing.
