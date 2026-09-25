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

Each entry cites the `REQ`(s) it verifies.

### Week 2 — superloop baseline (C0116-DK)

%% ---- Diagrama de flujo (Task A) ----

\begin{center}

\scalebox{0.65}{%

\begin{tikzpicture}[
    node distance=0.55cm,
    box/.style={
        draw,
        rectangle,
        rounded corners=3pt,
        align=flush left,
        text width=7.0cm,
        inner sep=6pt,
        font=\small
    },
    isr/.style={
        draw,
        rectangle,
        dashed,
        rounded corners=3pt,
        align=flush left,
        text width=7.0cm,
        inner sep=6pt,
        fill=orange!10,
        font=\small
    },
    decision/.style={
        draw,
        diamond,
        align=center,
        aspect=2.2,
        inner sep=2pt,
        font=\small,
        fill=green!10
    },
    arrow/.style={
        -{Stealth},
        thick
    }
]

\node (isr) [isr] {
    \textbf{ISR flags}\\
    • \textbf{Timer ISR:} incrementa \texttt{ticks\_pending} cada 1 ms\\
    • \textbf{Flow ISR:} incrementa \texttt{flow\_pulses} por cada pulso
};

\node (init) [box, below=of isr] {
    \textbf{Inicialización}\\
    \texttt{init\_hw()} configura GPIOs, ADC e interrupción de flujo.\\
    Se inicia el timer de 1 ms y comienza el \texttt{while(1)}.
};

\node (polled) [box, below=of init] {
    \textbf{Polled work}\\[2pt]
    \texttt{task\_console()}:
    \textbf{\texttt{instr\_cons}} = 1 al procesar $\rightarrow$ 0 al terminar\\
    \texttt{task\_display()}:
    \textbf{\texttt{instr\_disp}} = 1 al redibujar $\rightarrow$ 0 al terminar\\
    \texttt{task\_telemetry()}:
    \textbf{\texttt{instr\_tele}} = 1 al transmitir $\rightarrow$ 0 al terminar
};

\node (tick) [decision, below=of polled] {
    ¿\texttt{ticks\_pending}\\
    $>0$?
};

\node (sample) [box, below=of tick] {
    \textbf{Sampling / Control}\\
    Se consume 1 tick $\rightarrow$ \texttt{task\_sampling()}\\
    \textbf{\texttt{instr\_samp}}: 1 al entrar $\rightarrow$ 0 al salir\\
    Cada 10 muestras $\rightarrow$ \texttt{task\_control()}\\
    \textbf{\texttt{instr\_ctrl}}: 1 al entrar $\rightarrow$ 0 al salir
};

\node (flow) [box, below=of sample] {
    \textbf{Polled work: Flow}\\
    \texttt{task\_flow\_batch()} comprueba:
    \texttt{flow\_pulses >= 100}\\
    Si cumple: \textbf{\texttt{instr\_flow}} = 1 al entrar
    $\rightarrow$ 0 al terminar el cálculo
};

\draw [arrow] (isr) -- (init);
\draw [arrow] (init) -- (polled);
\draw [arrow] (polled) -- (tick);

\draw [arrow] (tick) --
    node[right] {\scriptsize Sí}
    (sample);

\coordinate (no_lane) at ([xshift=1.2cm]sample.east);
\draw [arrow]
    (tick.east) -- node[above] {\scriptsize No}
    (no_lane |- tick.east) |- (flow.east);

\draw [arrow] (sample) -- (flow);
\coordinate (loop_turn) at ([yshift=-0.55cm]flow.south);
\coordinate (loop_lane) at ([xshift=-2.2cm]polled.west);
\draw [arrow]
    (flow.south) -- (loop_turn) -- (loop_lane |- loop_turn)
    -- node[left] {\scriptsize Bucle} (loop_lane |- polled.west)
    -- (polled.west);

\end{tikzpicture}%

}

\end{center}

%% ---- Tabla resumen + fórmulas (Task B/C) ----

\begin{table}[H]
\centering
\caption{Resumen de mediciones del superloop}
\label{tab:mediciones_resumen}
\small
\renewcommand{\arraystretch}{1.4}
\setlength{\tabcolsep}{4pt}
\begin{tabularx}{\linewidth}{|>{\raggedright\arraybackslash}X|>{\centering\arraybackslash}p{3.5cm}|>{\raggedright\arraybackslash}X|}
\hline
\textbf{Medición} & \textbf{Mi valor} & \textbf{Referencia} \\
\hline
Período real de muestreo (nominal 1 kHz): promedio & 996.03 $\mu$s & 1000 $\mu$s \\
\hline
Jitter de muestreo: máximo durante $\geq 30$ s & 22578 $\mu$s & Registrar el valor obtenido; es la referencia del curso \\
\hline
Latencia ISR $\rightarrow$ atención del superloop (pulso de flujo) & 14.5 $\mu$s & Valor medido en el analizador lógico \\
\hline
Jitter de muestreo máximo con la caché de Flash desactivada & 24239 $\mu$s & La diferencia respecto al jitter base corresponde al acelerador ART \\
\hline
Jitter de muestreo con el comando bloqueante activo & 437588 $\mu$s & Comparar con el jitter base \\
\hline
\texttt{backlog\_peak}, en reposo $\rightarrow$ durante el comando bloqueante & 30 $\rightarrow$ 440 ticks & Misma situación, medida por el firmware \\
\hline
\end{tabularx}
\end{table}

Fórmulas usadas: Jitter máximo $=$ Max $-$ nominal (1000 $\mu$s); Latencia ISR
$=\Delta t$ entre flancos de CH0 y CH4 (marcador de tiempo); consistencia
firmware/analizador $\approx$ \texttt{backlog\_peak} $\times$ 1 ms.

%% ---- Captura base: cache ON (Task B) ----

\begin{figure}[H]
\centering
\begin{subfigure}[t]{0.48\linewidth}
    \centering
    \evidenceimage{logic1.png}
    \caption{Captura 1}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.48\linewidth}
    \centering
    \evidenceimage{logic2.png}
    \caption{Captura 2}
\end{subfigure}
\caption{Capturas del analizador lógico: ventana completa de 30 s, CH0 (\texttt{instr\_samp}), caché activa.}
\label{fig:analizador}
\end{figure}

\begin{table}[H]
\centering
\caption{Estadísticas de periodo del canal CH0 (\texttt{instr\_samp}), captura de 30 s}
\label{tab:stats_d3}
\small
\renewcommand{\arraystretch}{1.3}
\begin{tabular}{|l|r||l|r|}
\hline
$\Delta T$ & 30.087168 s & $N_{falling}$ & 30198 \\
\hline
$N_{rising}$ & 30198 & $f_{min}$ & 42.413 Hz \\
\hline
$f_{max}$ & 61776.062 Hz & $f_{mean}$ & 1003.981 Hz \\
\hline
$T_{std}$ & 1.0454 ms & Min & 16.19 $\mu$s \\
\hline
\textbf{Mean} & \textbf{996.03 $\mu$s} & Freq & 1003.981 Hz \\
\hline
SDev & 1045.42 $\mu$s & \textbf{Max} & \textbf{23577.75 $\mu$s} \\
\hline
Count & 30197 & & \\
\hline
\end{tabular}
\end{table}

\begin{figure}[H]
\centering
\evidenceimage{logic4.png}
\caption{Marcador de tiempo entre CH0 y CH4: $\Delta t = 14.5\ \mu$s (latencia ISR $\rightarrow$ atención del superloop).}
\label{fig:isr_latency}
\end{figure}

%% ---- Rebuild cache OFF (Task B) ----

\begin{figure}[H]
\centering
\begin{subfigure}[t]{0.48\linewidth}
    \centering
    \evidenceimage{logic5.png}
    \caption{Captura 1}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.48\linewidth}
    \centering
    \evidenceimage{logic6.png}
    \caption{Captura 2}
\end{subfigure}
\caption{Capturas del analizador lógico: ventana completa de 30 s, CH0 (\texttt{instr\_samp}), caché desactivada.}
\label{fig:analizador_nocache}
\end{figure}

\begin{table}[H]
\centering
\caption{Estadísticas de periodo del canal CH0 (\texttt{instr\_samp}), captura de 30 s, caché desactivada}
\label{tab:stats_nocache}
\small
\renewcommand{\arraystretch}{1.3}
\begin{tabular}{|l|r||l|r|}
\hline
$\Delta T$ & 30.108416 s & $N_{falling}$ & 30220 \\
\hline
$N_{rising}$ & 30220 & $f_{min}$ & 39.621 Hz \\
\hline
$f_{max}$ & 42553.191 Hz & $f_{mean}$ & 1003.706 Hz \\
\hline
$T_{std}$ & 1.1157 ms & Min & 23.50 $\mu$s \\
\hline
\textbf{Mean} & \textbf{996.31 $\mu$s} & Freq & 1003.706 Hz \\
\hline
SDev & 1115.66 $\mu$s & \textbf{Max} & \textbf{25239.44 $\mu$s} \\
\hline
Count & 30219 & & \\
\hline
\end{tabular}
\end{table}

%% ---- calib activo (Task C) ----

\begin{figure}[H]
\centering
\evidenceimage{logic7.png}
\caption{Captura del analizador lógico durante el disparo de \texttt{calib}, CH0 (\texttt{instr\_samp}).}
\label{fig:calib_capture}
\end{figure}

\begin{verbatim}
t=23000 ... backlog=30
calib
calibrating zero-flow offset (1000 rounds)...
calibration done
t=25000 ... backlog=440
...
status
p=1489 mV sp=1500 mV duty=45% flow_x100=0 estop=0
batches=0 backlog_peak=440
\end{verbatim}

\begin{table}[H]
\centering
\caption{Estadísticas de periodo del canal CH0 (\texttt{instr\_samp}), captura con \texttt{calib} activo}
\label{tab:stats_calib}
\small
\renewcommand{\arraystretch}{1.3}
\begin{tabular}{|l|r||l|r|}
\hline
$\Delta T$ & 20.015616 s & $N_{falling}$ & 20088 \\
\hline
$N_{rising}$ & 20088 & $f_{min}$ & 2.280 Hz \\
\hline
$f_{max}$ & 42553.191 Hz & $f_{mean}$ & 1003.635 Hz \\
\hline
$T_{std}$ & 3.2828 ms & Min & 23.50 $\mu$s \\
\hline
\textbf{Mean} & \textbf{996.38 $\mu$s} & Freq & 1003.635 Hz \\
\hline
SDev & 3282.80 $\mu$s & \textbf{Max} & \textbf{438588.31 $\mu$s} \\
\hline
Count & 20087 & & \\
\hline
\end{tabular}
\end{table}

Al ejecutar \texttt{calib}, \texttt{task\_console()} bloquea el superloop dentro
de \texttt{cmd\_calib()} ($\approx 1000$ rondas $\times$ 400 $\mu$s de
\texttt{k\_busy\_wait}), impidiendo que se drene \texttt{ticks\_pending}: el
backlog salta de 30 a 440 ticks y el jitter de \texttt{instr\_samp} pasa de
$\approx 22.6$ ms a $\approx 437.6$ ms, consistente entre analizador y firmware.

%% ---- Lectura de una línea ----

\textbf{Lectura:} con caché activa el superloop cumple 1 kHz con jitter de
orden decenas de ms (dominado por el peor pase del \texttt{while(1)}, no por el
ISR); desactivar la caché añade $\approx 1.7$ ms de jitter (costo del ART
accelerator); y el comando bloqueante \texttt{calib} degrada el jitter en dos
órdenes de magnitud ($\approx 437$ ms), mostrando el límite del superloop ante
una tarea firm mal comportada.

### Week 3 — S3 baseline and silicon comparison
…

## 4. Schedulability analysis

U = ΣC_i/T_i with **measured** C_i; test used (RM / hyperbolic / EDF); RTA as a
script with its output; blocking B_i if there are mutexes. (Formulas: READINGS.md,
"The math that does get used".)

## 5. Functional safety (final project)

Declared safe state (failure ⇒ valve closed), watchdog, and the evidence of the
fail-safe firing.
