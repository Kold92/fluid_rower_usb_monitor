<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { getActiveSession, getSessions, startSession, stopSession, getConfig, updateConfig } from '$lib/api';
  import { connectLiveStream } from '$lib/ws';
  import type { ActiveSession, LiveSample, LiveStats, SessionSummary, Config } from '$lib/types';
  import LiveChart from '$lib/components/LiveChart.svelte';

  let sessions: SessionSummary[] = [];
  let loadingSessions = true;
  let sessionError = '';
  let activeSession: ActiveSession | null = null;
  let sessionBusy = false;
  let sessionActionError = '';

  let latestSample: LiveSample | null = null;
  let latestStats: LiveStats | null = null;
  let strokeCount = 0;
  let wsStatus: 'connecting' | 'open' | 'closed' = 'connecting';
  let wsError = '';

  let powerChart: LiveChart;
  let spmChart: LiveChart;
  let splitTimeChart: LiveChart;

  let xAxisType: 'samples' | 'time' | 'distance' = 'samples';
  let maxPoints: number = 30;
  let powerXAxisData: (string | number)[] = [];
  let spmXAxisData: (string | number)[] = [];
  let splitTimeXAxisData: (string | number)[] = [];
  let cumulativeTimeArray: number[] = [];
  let cumulativeDistanceArray: number[] = [];

  const PRESET_POINTS = [10, 20, 30, 50, 100];

  function resetLiveView() {
    strokeCount = 0;
    latestSample = null;
    latestStats = null;
    powerXAxisData = [];
    spmXAxisData = [];
    splitTimeXAxisData = [];
    cumulativeTimeArray = [];
    cumulativeDistanceArray = [];
    powerChart?.reset();
    spmChart?.reset();
    splitTimeChart?.reset();
  }

  function regenerateXAxisData() {
    const newPowerData: (string | number)[] = [];
    const newSpmData: (string | number)[] = [];
    const newSplitTimeData: (string | number)[] = [];

    if (xAxisType === 'samples') {
      for (let i = 0; i < strokeCount; i++) {
        newPowerData.push(`#${i + 1}`);
        newSpmData.push(`#${i + 1}`);
        newSplitTimeData.push(`#${i + 1}`);
      }
    } else if (xAxisType === 'time' && cumulativeTimeArray.length > 0) {
      for (let i = 0; i < cumulativeTimeArray.length; i++) {
        newPowerData.push(Math.floor(cumulativeTimeArray[i]));
        newSpmData.push(Math.floor(cumulativeTimeArray[i]));
        newSplitTimeData.push(Math.floor(cumulativeTimeArray[i]));
      }
    } else if (xAxisType === 'distance' && cumulativeDistanceArray.length > 0) {
      for (let i = 0; i < cumulativeDistanceArray.length; i++) {
        newPowerData.push(cumulativeDistanceArray[i].toFixed(1));
        newSpmData.push(cumulativeDistanceArray[i].toFixed(1));
        newSplitTimeData.push(cumulativeDistanceArray[i].toFixed(1));
      }
    }

    powerXAxisData = newPowerData;
    spmXAxisData = newSpmData;
    splitTimeXAxisData = newSplitTimeData;
    powerChart?.updateLabels(newPowerData);
    spmChart?.updateLabels(newSpmData);
    splitTimeChart?.updateLabels(newSplitTimeData);
  }

  function computeXAxisValue(): string | number {
    if (xAxisType === 'samples') {
      return `#${strokeCount}`;
    } else if (xAxisType === 'time' && latestStats) {
      return Math.floor(latestStats.total_duration_secs);
    } else if (xAxisType === 'distance' && latestStats) {
      return latestStats.total_distance_m.toFixed(1);
    }
    return `#${strokeCount}`;
  }

  function formatSplitTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }


  async function handleXAxisChange(newType: 'samples' | 'time' | 'distance') {
    xAxisType = newType;
    // Save to config
    try {
      await updateConfig({ ui: { x_axis_type: newType, max_points: maxPoints } });
    } catch (err) {
      console.error('Failed to save x-axis preference:', err);
    }
    // Regenerate axis data without clearing chart data
    regenerateXAxisData();
  }

  async function handleMaxPointsChange(newMax: number) {
    maxPoints = newMax;
    // Save to config
    try {
      await updateConfig({ ui: { x_axis_type: xAxisType, max_points: newMax } });
    } catch (err) {
      console.error('Failed to save max points preference:', err);
    }
  }

  async function refreshActiveSession() {
    try {
      activeSession = await getActiveSession();
    } catch (err) {
      sessionActionError = (err as Error).message;
    }
  }

  async function handleStartSession() {
    sessionBusy = true;
    sessionActionError = '';
    try {
      activeSession = await startSession();
      resetLiveView();
    } catch (err) {
      sessionActionError = (err as Error).message;
    } finally {
      sessionBusy = false;
    }
  }

  async function handleStopSession() {
    sessionBusy = true;
    sessionActionError = '';
    try {
      await stopSession();
      activeSession = null;
      sessions = await getSessions();
    } catch (err) {
      sessionActionError = (err as Error).message;
    } finally {
      sessionBusy = false;
    }
  }

  onMount(async () => {
    try {
      sessions = await getSessions();
    } catch (err) {
      sessionError = (err as Error).message;
    } finally {
      loadingSessions = false;
    }

    await refreshActiveSession();

    // Load x-axis preference
    try {
      const config = await getConfig();
      if (config.ui?.x_axis_type) {
        xAxisType = config.ui.x_axis_type;
      }
      if (config.ui?.max_points) {
        maxPoints = config.ui.max_points;
      }
    } catch (err) {
      console.error('Failed to load config:', err);
    }

    const disconnect = connectLiveStream({
      onSample: (sample) => {
        latestSample = sample;
        strokeCount += 1;
        wsStatus = 'open';
        
        const xValue = computeXAxisValue();
        powerXAxisData.push(xValue);
        spmXAxisData.push(xValue);
        splitTimeXAxisData.push(xValue);
        
        // Update charts
        powerChart?.addPoint(sample.power_watts, strokeCount);
        spmChart?.addPoint(sample.strokes_per_min, strokeCount);
        splitTimeChart?.addPoint(sample.time_500m_secs, strokeCount);
      },
      onStats: (stats) => {
        latestStats = stats;
        cumulativeTimeArray.push(stats.total_duration_secs);
        cumulativeDistanceArray.push(stats.total_distance_m);
      },
      onSession: (session) => {
        activeSession = session;
        resetLiveView();
      },
      onError: (err) => {
        wsError = err.message;
      },
      onClose: () => {
        wsStatus = 'closed';
      }
    });

    return () => disconnect();
  });
</script>

<svelte:head>
  <title>Fluid Rower Monitor</title>
</svelte:head>

<main class="min-h-screen bg-gradient-to-b from-bg-base via-bg-elevated to-bg-base text-text-primary">
  <div class="max-w-6xl mx-auto px-4 py-10 space-y-8">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-text-secondary text-sm">Network-ready · Real-time · Dev Mode</p>
        <h1 class="text-3xl font-bold">Fluid Rower Monitor</h1>
      </div>
      <div class="flex gap-2 text-sm">
        <span class="px-3 py-1 rounded-full border border-border bg-bg-card">API: http://localhost:8000</span>
        <span class="px-3 py-1 rounded-full" class:bg-success={wsStatus === 'open'} class:bg-warning={wsStatus === 'connecting'} class:bg-danger={wsStatus === 'closed'}>
          WS: {wsStatus}
        </span>
      </div>
    </header>

    <section class="card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-text-secondary text-sm">Session</p>
        {#if activeSession}
          <p class="text-lg font-semibold">Active</p>
          <p class="text-text-secondary text-sm">Started: {new Date(activeSession.start).toLocaleString('en-GB', { hour12: false })}</p>
          <p class="text-text-muted text-xs">ID: {activeSession.id}</p>
        {:else}
          <p class="text-lg font-semibold">Not active</p>
          <p class="text-text-secondary text-sm">Ready to start a new session</p>
        {/if}
        {#if sessionActionError}
          <p class="text-danger text-sm">{sessionActionError}</p>
        {/if}
      </div>
      <div class="flex gap-2">
        <button
          class="btn bg-success hover:bg-success/90 disabled:opacity-50"
          on:click={handleStartSession}
          disabled={sessionBusy || !!activeSession}
        >
          Start Session
        </button>
        <button
          class="btn bg-danger hover:bg-danger/90 disabled:opacity-50"
          on:click={handleStopSession}
          disabled={sessionBusy || !activeSession}
        >
          Stop Session
        </button>
      </div>
    </section>

    <!-- X-Axis Selector -->
    <section class="card">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex items-center gap-4">
          <p class="text-text-secondary text-sm">X-Axis:</p>
          <div class="flex gap-2">
            <button
              class="px-3 py-1 rounded-md text-sm font-medium transition"
              class:bg-primary={xAxisType === 'samples'}
              class:text-primary={xAxisType !== 'samples'}
              class:bg-bg-elevated={xAxisType !== 'samples'}
              on:click={() => handleXAxisChange('samples')}
            >
              Samples
            </button>
            <button
              class="px-3 py-1 rounded-md text-sm font-medium transition"
              class:bg-primary={xAxisType === 'time'}
              class:text-primary={xAxisType !== 'time'}
              class:bg-bg-elevated={xAxisType !== 'time'}
              on:click={() => handleXAxisChange('time')}
            >
              Time (s)
            </button>
            <button
              class="px-3 py-1 rounded-md text-sm font-medium transition"
              class:bg-primary={xAxisType === 'distance'}
              class:text-primary={xAxisType !== 'distance'}
              class:bg-bg-elevated={xAxisType !== 'distance'}
              on:click={() => handleXAxisChange('distance')}
            >
              Distance (m)
            </button>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <p class="text-text-secondary text-sm">History:</p>
          <div class="flex gap-1">
            {#each PRESET_POINTS as preset}
              <button
                class="px-2 py-1 rounded text-xs font-medium transition"
                class:bg-primary={maxPoints === preset}
                class:text-primary={maxPoints !== preset}
                class:bg-bg-elevated={maxPoints !== preset}
                on:click={() => handleMaxPointsChange(preset)}
              >
                {preset}
              </button>
            {/each}
          </div>
          <input
            type="number"
            min="10"
            max="500"
            value={maxPoints}
            on:change={(e) => handleMaxPointsChange(parseInt(e.currentTarget.value) || 30)}
            class="w-16 px-2 py-1 rounded text-sm bg-bg-elevated border border-border text-text-primary"
          />
        </div>
      </div>
    </section>

    <!-- Charts Section -->
    <section class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <LiveChart bind:this={powerChart} title="Power" unit="W" label="Watts" color="rgb(239, 68, 68)" {maxPoints} yMin={0} yMax={400} latestValue={latestSample?.power_watts} xAxisData={powerXAxisData} />
      <LiveChart bind:this={spmChart} title="Stroke Rate" unit="spm" label="SPM" color="rgb(14, 165, 233)" {maxPoints} yMin={0} yMax={35} latestValue={latestSample?.strokes_per_min} xAxisData={spmXAxisData} />
      <LiveChart bind:this={splitTimeChart} title="Split Time" unit="/500m" label="Time" color="rgb(168, 85, 247)" {maxPoints} yMin={60} yMax={300} latestValue={latestSample?.time_500m_secs ?? 0} formatter={formatSplitTime} xAxisData={splitTimeXAxisData} />
    </section>

    <section class="grid gap-6" class:md:grid-cols-2={!activeSession}>
      <div class="card space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold">Current Stats</h2>
          {#if wsError}
            <span class="text-danger text-sm">{wsError}</span>
          {/if}
        </div>
        {#if latestStats}
          <div class="grid grid-cols-2 gap-3 text-sm md:grid-cols-3" class:lg:grid-cols-4={activeSession}>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Total Distance</p>
              <p class="text-2xl font-semibold">{latestStats.total_distance_m.toFixed(1)} m</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Total Duration</p>
              <p class="text-2xl font-semibold">{Math.floor(latestStats.total_duration_secs / 60)}:{(latestStats.total_duration_secs % 60).toFixed(0).padStart(2, '0')}</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Avg Split Time</p>
              <p class="text-2xl font-semibold">{formatSplitTime(latestStats.avg_time_500m_secs)}</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Avg Power</p>
              <p class="text-2xl font-semibold">{latestStats.avg_watts.toFixed(1)} W</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Max Power</p>
              <p class="text-2xl font-semibold">{latestStats.max_watts} W</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Calories</p>
              <p class="text-2xl font-semibold">{latestStats.total_calories.toFixed(1)}</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Avg Stroke Rate</p>
              <p class="text-2xl font-semibold">{latestStats.avg_strokes_per_min.toFixed(1)} spm</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Max Stroke Rate</p>
              <p class="text-2xl font-semibold">{latestStats.max_strokes_per_min} spm</p>
            </div>
          </div>
          <p class="text-text-secondary text-sm">Total strokes: {latestStats.num_strokes}</p>
        {:else if latestSample}
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Power</p>
              <p class="text-2xl font-semibold">{latestSample.power_watts} W</p>
            </div>
            <div class="card bg-bg-elevated/80">
              <p class="text-text-secondary">Stroke Rate</p>
              <p class="text-2xl font-semibold">{latestSample.strokes_per_min} spm</p>
            </div>
          </div>
          <p class="text-text-secondary text-sm">Total strokes received: {strokeCount}</p>
        {:else}
          <p class="text-text-secondary text-sm">Waiting for first sample...</p>
        {/if}
      </div>

      {#if !activeSession}
        <div class="card space-y-3">
          <h2 class="text-xl font-semibold">Sessions</h2>
          {#if loadingSessions}
            <p class="text-text-secondary text-sm">Loading sessions...</p>
          {:else if sessionError}
            <p class="text-danger text-sm">{sessionError}</p>
          {:else if sessions.length === 0}
            <p class="text-text-secondary text-sm">No sessions found yet.</p>
          {:else}
            <ul class="space-y-2">
              {#each sessions as session}
                <li class="py-2 flex justify-between text-sm">
                  <span>{session.id}</span>
                  {#if session.start}
                    <span class="text-text-secondary">{session.start}</span>
                  {/if}
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      {/if}
    </section>
  </div>
</main>
