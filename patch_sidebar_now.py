with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "r") as f:
    content = f.read()

old_label = """            <div className="space-y-1">
              <label className="text-[#8FA8B8]">Departure</label>
              <input"""

new_label = """            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className="text-[#8FA8B8]">Departure</label>
                <button 
                  type="button"
                  onClick={() => setDepartureTime && setDepartureTime(new Date().toISOString())} 
                  className="text-[#00D4FF] hover:text-[#EAF4F8] text-[9px] uppercase font-bold cursor-pointer"
                >
                  [ Now ]
                </button>
              </div>
              <input"""

content = content.replace(old_label, new_label)

with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "w") as f:
    f.write(content)
print("RoutingSidebar Now button patched")
