export function ReasoningTree() {
  return (
    <div className="font-mono text-xs leading-5 text-muted-foreground">
      <div className="text-foreground font-semibold mb-2">Repository Understanding</div>
      
      <div className="pl-2 border-l border-border ml-2 space-y-4">
        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Structure Analysis</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Modules
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Dependencies
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Layers
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Boundaries
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Runtime Analysis</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Entry Points
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Request Flow
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Data Flow
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Control Flow
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Design Reasoning</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Key Patterns
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Tradeoffs
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Architectural Choices
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Alternatives
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Developer Onboarding</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Learning Path
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Critical Files
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Important Concepts
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Contribution Guide
            </div>
          </div>
        </div>
        
        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Risk Assessment</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Complexity Hotspots
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Coupling
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Single Points of Failure
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Maintenance Risks
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
