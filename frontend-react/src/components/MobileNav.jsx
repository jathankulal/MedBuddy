import {
  Home,
  Pill,
  FileText,
  HeartPulse,
} from 'lucide-react';

const tabs = [
  { label: 'Home', page: 'Dashboard', icon: Home },
  { label: 'Medicines', page: 'Medications', icon: Pill },
  { label: 'Documents', page: 'Documents', icon: FileText },
  { label: 'My Health', page: 'Health Profile', icon: HeartPulse },
];

export default function MobileNav({ active, onNavigate }) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white px-2 shadow-lg">
      <div className="mx-auto flex max-w-lg items-center justify-around py-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const selected = active === tab.page;

          return (
            <button
              key={tab.page}
              type="button"
              onClick={() => onNavigate(tab.page)}
              className={`flex flex-1 flex-col items-center gap-1 rounded-xl px-1 py-2 ${
                selected ? 'text-emerald-700' : 'text-gray-400'
              }`}
            >
              <Icon size={22} />
              <span className="text-[11px] font-medium">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
