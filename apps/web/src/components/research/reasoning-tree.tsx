export function ReasoningTree() {
  return (
    <div className="font-mono text-xs leading-5 text-muted-foreground">
      <div className="text-foreground font-semibold mb-2">Repository Understanding</div>
      
      <div className="pl-2 border-l border-border ml-2 space-y-4">
        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Architecture</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Services
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Modules
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Dependencies
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Execution Flow</span>
          </div>
          <div className="pl-6 border-l border-border ml-2 space-y-1 mt-1">
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Entry Points
            </div>
            <div className="flex items-center">
              <span className="w-4 border-t border-border inline-block mr-2"></span>
              Request Lifecycle
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Design Decisions</span>
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <span className="w-4 border-t border-border inline-block mr-2"></span>
            <span className="text-foreground font-medium">Contributor Guide</span>
          </div>
        </div>
      </div>
    </div>
  )
}
