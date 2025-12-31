import SwiftUI

// MARK: - Portfolio Manager App

/// The main application entry point for Portfolio Manager.
///
/// Configures the app with:
/// - Main window with ContentView
/// - PortfolioStore as environment object
/// - macOS window styling and commands
@main
struct PortfolioManagerApp: App {
    
    // MARK: - State
    
    /// The shared portfolio store managing all application data.
    @StateObject private var store = PortfolioStore()
    
    // MARK: - Body
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
        }
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified(showsTitle: true))
        .commands {
            SidebarCommands()
        }
    }
}

