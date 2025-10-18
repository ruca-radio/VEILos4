import React, { useEffect, useMemo, useRef, useState } from "react";

// VEILos4 — Ultra-Modern Terminal Console
// Smooth fonts, fade effects, graphics rendering, animations

interface BootSettings {
  userMode: "user" | "sudo";
  networkEnabled: boolean;
  pluginManagerEnabled: boolean;
  multimodelEnabled: boolean;
  mixModelEnabled: boolean;
  agenticEnabled: boolean;
  memoryPersistence: boolean;
  postgresqlDSN: string;
  providers: Array<{
    name: string;
    baseURL: string;
    apiKey: string;
    model: string;
  }>;
  vosFile: File | null;
  launchURL: string;
}

interface TerminalLine {
  id: string;
  type: "command" | "output" | "error" | "system";
  content: string;
  timestamp: Date;
}

interface CommandHistory {
  commands: string[];
  currentIndex: number;
}

function VeilosTerminalConsole() {
  // ---------- Boot State ----------
  const [showBootloader, setShowBootloader] = useState(true);
  const [bootPhase, setBootPhase] = useState<"splash" | "settings" | "loading" | "done">("splash");
  const [bootSettings, setBootSettings] = useState<BootSettings>({
    userMode: "user",
    networkEnabled: true,
    pluginManagerEnabled: true,
    multimodelEnabled: false,
    mixModelEnabled: false,
    agenticEnabled: false,
    memoryPersistence: false,
    postgresqlDSN: "",
    providers: Array(5).fill(null).map(() => ({ 
      name: "", 
      baseURL: "", 
      apiKey: "", 
      model: "" 
    })),
    vosFile: null,
    launchURL: "https://github.com/ruca-radio/VEILos4/start.vsh"
  });

  // ---------- Core State ----------
  const [booted, setBooted] = useState(false);
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [currentCommand, setCurrentCommand] = useState("");
  const [history, setHistory] = useState<CommandHistory>({
    commands: [],
    currentIndex: -1
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [veil4Connected, setVeil4Connected] = useState(false);

  // ---------- Refs ----------
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const bootLoaderTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // ---------- Boot Sequence ----------
  useEffect(() => {
    if (!showBootloader) return;

    const runBootSequence = async () => {
      // Splash phase - 2 seconds
      await sleep(2000);
      setBootPhase("settings");
    };

    runBootSequence();
  }, []);

  const handleBootComplete = async () => {
    setBootPhase("loading");
    
    // Simulate initialization
    await sleep(1500);
    
    setBootPhase("done");
    await sleep(500);
    
    setShowBootloader(false);
    setBooted(true);
    
    // Add welcome messages
    addSystemLine("VEILos4 Quantum-Cognitive Operating System");
    addSystemLine(`Version 1.0.0 | ${new Date().toISOString()}`);
    addSystemLine("═".repeat(60));
    addSystemLine("Initializing quantum substrate...");
    
    await sleep(300);
    
    try {
      // Attempt to connect to VEIL4 backend
      const connected = await initializeVEIL4();
      setVeil4Connected(connected);
      
      if (connected) {
        addSystemLine("✓ Quantum substrate initialized");
        addSystemLine("✓ Capability security layer active");
        addSystemLine("✓ Extensibility framework loaded");
        addSystemLine("✓ Cognitive parity established");
        addSystemLine("✓ Audit transparency enabled");
      } else {
        addSystemLine("⚠ Running in standalone mode (backend not available)");
      }
    } catch (error) {
      addSystemLine("⚠ Error initializing VEIL4 backend");
      console.error(error);
    }
    
    addSystemLine("═".repeat(60));
    addSystemLine(`Ready. Type 'help' for available commands.`);
    addSystemLine("");
  };

  // ---------- VEIL4 Integration ----------
  const initializeVEIL4 = async (): Promise<boolean> => {
    try {
      // In a real implementation, this would connect to the Python backend
      // For now, we'll simulate the connection
      
      // Check if running in a context with VEIL4 backend available
      const response = await fetch('/api/veil4/status', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      }).catch(() => null);
      
      if (response && response.ok) {
        const status = await response.json();
        return status.running === true;
      }
      
      return false;
    } catch (error) {
      return false;
    }
  };

  const executeVEIL4Command = async (command: string): Promise<string> => {
    if (!veil4Connected) {
      return "VEIL4 backend not connected. Running in standalone mode.";
    }

    try {
      const response = await fetch('/api/veil4/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          command,
          settings: bootSettings 
        })
      });

      if (response.ok) {
        const result = await response.json();
        return result.output || "Command executed successfully.";
      } else {
        return `Error: ${response.statusText}`;
      }
    } catch (error) {
      return `Error executing command: ${error}`;
    }
  };

  // ---------- Terminal Operations ----------
  const addLine = (type: TerminalLine["type"], content: string) => {
    const newLine: TerminalLine = {
      id: `line-${Date.now()}-${Math.random()}`,
      type,
      content,
      timestamp: new Date()
    };
    setLines(prev => [...prev, newLine]);
    
    // Auto-scroll to bottom
    setTimeout(() => {
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    }, 0);
  };

  const addSystemLine = (content: string) => addLine("system", content);
  const addOutputLine = (content: string) => addLine("output", content);
  const addErrorLine = (content: string) => addLine("error", content);

  const processCommand = async (cmd: string) => {
    if (!cmd.trim()) return;

    // Add command to display
    addLine("command", `$ ${cmd}`);

    // Add to history
    setHistory(prev => ({
      commands: [...prev.commands, cmd],
      currentIndex: -1
    }));

    setIsProcessing(true);

    try {
      // Parse and execute command
      const result = await executeCommand(cmd);
      if (result) {
        addOutputLine(result);
      }
    } catch (error) {
      addErrorLine(`Error: ${error}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const executeCommand = async (cmd: string): Promise<string> => {
    const parts = cmd.trim().split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    switch (command) {
      case "help":
        return getHelpText();
      
      case "clear":
        setLines([]);
        return "";
      
      case "status":
        return getSystemStatus();
      
      case "quantum":
        return await handleQuantumCommand(args);
      
      case "capability":
        return await handleCapabilityCommand(args);
      
      case "agent":
        return await handleAgentCommand(args);
      
      case "plugin":
        return await handlePluginCommand(args);
      
      case "echo":
        return args.join(" ");
      
      case "veil4":
        return await executeVEIL4Command(args.join(" "));
      
      default:
        return `Unknown command: ${command}. Type 'help' for available commands.`;
    }
  };

  const getHelpText = (): string => {
    return `
VEILos4 Terminal Commands:
════════════════════════════════════════════════════════════

Basic Commands:
  help                    - Show this help message
  clear                   - Clear the terminal
  status                  - Show system status
  echo <message>          - Echo a message

Quantum Commands:
  quantum create <id>     - Create a quantum superposition
  quantum observe <id>    - Observe and collapse a quantum state
  quantum list            - List active quantum states

Capability Commands:
  capability grant <agent> <resource> <perms>
                          - Grant capability to an agent
  capability verify <token>
                          - Verify a capability token

Agent Commands:
  agent register <id> <type>
                          - Register a new agent (human/model)
  agent list              - List all registered agents

Plugin Commands:
  plugin list             - List loaded plugins
  plugin load <name>      - Load a plugin
  plugin unload <name>    - Unload a plugin

VEIL4 Backend:
  veil4 <command>         - Execute command on VEIL4 backend
  
════════════════════════════════════════════════════════════`;
  };

  const getSystemStatus = (): string => {
    return `
System Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Boot Configuration:
  User Mode:              ${bootSettings.userMode}
  Network:                ${bootSettings.networkEnabled ? "Enabled" : "Disabled"}
  Plugin Manager:         ${bootSettings.pluginManagerEnabled ? "Enabled" : "Disabled"}
  Multi-model:            ${bootSettings.multimodelEnabled ? "Enabled" : "Disabled"}
  Mix Model:              ${bootSettings.mixModelEnabled ? "Enabled" : "Disabled"}
  Agentic Mode:           ${bootSettings.agenticEnabled ? "Enabled" : "Disabled"}
  Memory Persistence:     ${bootSettings.memoryPersistence ? "Enabled" : "Disabled"}

Connection:
  VEIL4 Backend:          ${veil4Connected ? "Connected" : "Disconnected"}
  Launch URL:             ${bootSettings.launchURL}

Terminal:
  Lines:                  ${lines.length}
  Commands in History:    ${history.commands.length}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
  };

  const handleQuantumCommand = async (args: string[]): Promise<string> => {
    const subcommand = args[0];
    
    switch (subcommand) {
      case "create":
        return "Quantum state created (simulated in frontend)";
      case "observe":
        return "Quantum state observed and collapsed (simulated)";
      case "list":
        return "No active quantum states (connect to backend for full functionality)";
      default:
        return "Usage: quantum <create|observe|list> [args]";
    }
  };

  const handleCapabilityCommand = async (args: string[]): Promise<string> => {
    const subcommand = args[0];
    
    switch (subcommand) {
      case "grant":
        return "Capability granted (simulated)";
      case "verify":
        return "Capability verified (simulated)";
      default:
        return "Usage: capability <grant|verify> [args]";
    }
  };

  const handleAgentCommand = async (args: string[]): Promise<string> => {
    const subcommand = args[0];
    
    switch (subcommand) {
      case "register":
        return "Agent registered (simulated)";
      case "list":
        return "No agents registered (connect to backend for full functionality)";
      default:
        return "Usage: agent <register|list> [args]";
    }
  };

  const handlePluginCommand = async (args: string[]): Promise<string> => {
    const subcommand = args[0];
    
    switch (subcommand) {
      case "list":
        return "No plugins loaded (connect to backend for full functionality)";
      case "load":
        return "Plugin loaded (simulated)";
      case "unload":
        return "Plugin unloaded (simulated)";
      default:
        return "Usage: plugin <list|load|unload> [args]";
    }
  };

  // ---------- Input Handling ----------
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (currentCommand.trim() && !isProcessing) {
        processCommand(currentCommand);
        setCurrentCommand("");
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      navigateHistory("up");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      navigateHistory("down");
    } else if (e.key === "Tab") {
      e.preventDefault();
      // Tab completion could be added here
    }
  };

  const navigateHistory = (direction: "up" | "down") => {
    if (history.commands.length === 0) return;

    setHistory(prev => {
      let newIndex = prev.currentIndex;
      
      if (direction === "up") {
        newIndex = prev.currentIndex === -1 
          ? prev.commands.length - 1 
          : Math.max(0, prev.currentIndex - 1);
      } else {
        newIndex = prev.currentIndex === -1 
          ? -1 
          : Math.min(prev.commands.length - 1, prev.currentIndex + 1);
      }

      const command = newIndex === -1 ? "" : prev.commands[newIndex];
      setCurrentCommand(command);

      return { ...prev, currentIndex: newIndex };
    });
  };

  // ---------- Utilities ----------
  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  // ---------- Bootloader UI ----------
  if (showBootloader) {
    return (
      <div style={styles.bootloader}>
        {bootPhase === "splash" && (
          <div style={styles.splash}>
            <div style={styles.logo}>
              <div style={styles.logoText}>VEILos4</div>
              <div style={styles.subtitle}>Quantum-Cognitive Operating System</div>
            </div>
            <div style={styles.spinner}>⟳</div>
          </div>
        )}

        {bootPhase === "settings" && (
          <div style={styles.settings}>
            <h2 style={styles.settingsTitle}>Boot Configuration</h2>
            
            <div style={styles.settingsGrid}>
              <div style={styles.settingRow}>
                <label style={styles.label}>User Mode:</label>
                <select 
                  style={styles.select}
                  value={bootSettings.userMode}
                  onChange={(e) => setBootSettings({...bootSettings, userMode: e.target.value as "user" | "sudo"})}
                >
                  <option value="user">User</option>
                  <option value="sudo">Sudo</option>
                </select>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>
                  <input
                    type="checkbox"
                    checked={bootSettings.networkEnabled}
                    onChange={(e) => setBootSettings({...bootSettings, networkEnabled: e.target.checked})}
                    style={styles.checkbox}
                  />
                  Network Enabled
                </label>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>
                  <input
                    type="checkbox"
                    checked={bootSettings.pluginManagerEnabled}
                    onChange={(e) => setBootSettings({...bootSettings, pluginManagerEnabled: e.target.checked})}
                    style={styles.checkbox}
                  />
                  Plugin Manager
                </label>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>
                  <input
                    type="checkbox"
                    checked={bootSettings.multimodelEnabled}
                    onChange={(e) => setBootSettings({...bootSettings, multimodelEnabled: e.target.checked})}
                    style={styles.checkbox}
                  />
                  Multi-model Support
                </label>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>
                  <input
                    type="checkbox"
                    checked={bootSettings.mixModelEnabled}
                    onChange={(e) => setBootSettings({...bootSettings, mixModelEnabled: e.target.checked})}
                    style={styles.checkbox}
                  />
                  Mix Model
                </label>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>
                  <input
                    type="checkbox"
                    checked={bootSettings.agenticEnabled}
                    onChange={(e) => setBootSettings({...bootSettings, agenticEnabled: e.target.checked})}
                    style={styles.checkbox}
                  />
                  Agentic Mode
                </label>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>
                  <input
                    type="checkbox"
                    checked={bootSettings.memoryPersistence}
                    onChange={(e) => setBootSettings({...bootSettings, memoryPersistence: e.target.checked})}
                    style={styles.checkbox}
                  />
                  Memory Persistence
                </label>
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>PostgreSQL DSN:</label>
                <input
                  type="text"
                  style={styles.input}
                  value={bootSettings.postgresqlDSN}
                  onChange={(e) => setBootSettings({...bootSettings, postgresqlDSN: e.target.value})}
                  placeholder="postgresql://user:pass@host:5432/db"
                />
              </div>

              <div style={styles.settingRow}>
                <label style={styles.label}>Launch URL:</label>
                <input
                  type="text"
                  style={styles.input}
                  value={bootSettings.launchURL}
                  onChange={(e) => setBootSettings({...bootSettings, launchURL: e.target.value})}
                />
              </div>
            </div>

            <button 
              style={styles.button}
              onClick={handleBootComplete}
            >
              Boot System
            </button>
          </div>
        )}

        {bootPhase === "loading" && (
          <div style={styles.loading}>
            <div style={styles.loadingText}>Initializing VEILos4...</div>
            <div style={styles.progressBar}>
              <div style={styles.progressFill}></div>
            </div>
          </div>
        )}

        {bootPhase === "done" && (
          <div style={styles.done}>
            <div style={styles.doneText}>✓ Boot Complete</div>
          </div>
        )}
      </div>
    );
  }

  // ---------- Terminal UI ----------
  return (
    <div style={styles.container}>
      <div style={styles.terminal} ref={terminalRef}>
        {lines.map(line => (
          <div key={line.id} style={styles.line}>
            <span style={getLineStyle(line.type)}>
              {line.content}
            </span>
          </div>
        ))}
        
        <div style={styles.inputLine}>
          <span style={styles.prompt}>$</span>
          <input
            ref={inputRef}
            type="text"
            style={styles.terminalInput}
            value={currentCommand}
            onChange={(e) => setCurrentCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isProcessing}
            autoFocus
          />
          {isProcessing && <span style={styles.spinner}>⟳</span>}
        </div>
      </div>
    </div>
  );
}

const getLineStyle = (type: TerminalLine["type"]): React.CSSProperties => {
  const baseStyle: React.CSSProperties = {
    fontFamily: "'Fira Code', 'Monaco', 'Courier New', monospace",
    fontSize: "14px",
    lineHeight: "1.6",
    whiteSpace: "pre-wrap",
    wordWrap: "break-word",
  };

  switch (type) {
    case "command":
      return { ...baseStyle, color: "#4CAF50", fontWeight: "bold" };
    case "output":
      return { ...baseStyle, color: "#E0E0E0" };
    case "error":
      return { ...baseStyle, color: "#F44336" };
    case "system":
      return { ...baseStyle, color: "#00BCD4" };
    default:
      return baseStyle;
  }
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    width: "100%",
    height: "100vh",
    backgroundColor: "#1E1E1E",
    display: "flex",
    flexDirection: "column",
  },
  terminal: {
    flex: 1,
    padding: "20px",
    overflowY: "auto",
    fontFamily: "'Fira Code', 'Monaco', 'Courier New', monospace",
    fontSize: "14px",
    color: "#E0E0E0",
  },
  line: {
    marginBottom: "4px",
  },
  inputLine: {
    display: "flex",
    alignItems: "center",
    marginTop: "8px",
  },
  prompt: {
    color: "#4CAF50",
    marginRight: "8px",
    fontWeight: "bold",
  },
  terminalInput: {
    flex: 1,
    backgroundColor: "transparent",
    border: "none",
    outline: "none",
    color: "#E0E0E0",
    fontFamily: "'Fira Code', 'Monaco', 'Courier New', monospace",
    fontSize: "14px",
  },
  spinner: {
    marginLeft: "8px",
    color: "#00BCD4",
    animation: "spin 1s linear infinite",
  },
  
  // Bootloader styles
  bootloader: {
    width: "100%",
    height: "100vh",
    backgroundColor: "#0D1117",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#E0E0E0",
  },
  splash: {
    textAlign: "center",
  },
  logo: {
    marginBottom: "40px",
  },
  logoText: {
    fontSize: "64px",
    fontWeight: "bold",
    background: "linear-gradient(45deg, #00BCD4, #4CAF50)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    marginBottom: "16px",
  },
  subtitle: {
    fontSize: "18px",
    color: "#888",
  },
  settings: {
    maxWidth: "600px",
    width: "90%",
    padding: "40px",
    backgroundColor: "#161B22",
    borderRadius: "8px",
    boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
  },
  settingsTitle: {
    fontSize: "32px",
    marginBottom: "32px",
    textAlign: "center",
    color: "#00BCD4",
  },
  settingsGrid: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    marginBottom: "32px",
  },
  settingRow: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "14px",
    color: "#E0E0E0",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  select: {
    padding: "8px 12px",
    backgroundColor: "#0D1117",
    border: "1px solid #30363D",
    borderRadius: "4px",
    color: "#E0E0E0",
    fontSize: "14px",
  },
  checkbox: {
    width: "16px",
    height: "16px",
  },
  input: {
    padding: "8px 12px",
    backgroundColor: "#0D1117",
    border: "1px solid #30363D",
    borderRadius: "4px",
    color: "#E0E0E0",
    fontSize: "14px",
    width: "100%",
  },
  button: {
    width: "100%",
    padding: "12px 24px",
    backgroundColor: "#00BCD4",
    border: "none",
    borderRadius: "4px",
    color: "#0D1117",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    transition: "all 0.3s ease",
  },
  loading: {
    textAlign: "center",
  },
  loadingText: {
    fontSize: "24px",
    marginBottom: "24px",
    color: "#00BCD4",
  },
  progressBar: {
    width: "300px",
    height: "4px",
    backgroundColor: "#30363D",
    borderRadius: "2px",
    overflow: "hidden",
  },
  progressFill: {
    width: "100%",
    height: "100%",
    backgroundColor: "#00BCD4",
    animation: "progress 1.5s ease-in-out",
  },
  done: {
    textAlign: "center",
  },
  doneText: {
    fontSize: "32px",
    color: "#4CAF50",
  },
};

export default VeilosTerminalConsole;
