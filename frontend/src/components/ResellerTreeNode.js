import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, Trash2, ArrowRightLeft } from 'lucide-react';

const ResellerTreeNode = ({ reseller, level, expandedResellers, toggleExpand, handleDeleteReseller, setTransferModal }) => {
  const isExpanded = expandedResellers.has(reseller.id);
  const hasChildren = reseller.children && reseller.children.length > 0;
  
  return (
    <div>
      <div 
        className={`flex items-center gap-2 p-3 rounded-lg hover:bg-slate-50 transition-colors ${
          level > 0 ? 'ml-' + (level * 6) : ''
        }`}
        style={{ marginLeft: `${level * 24}px` }}
      >
        {/* Expand/Collapse */}
        {hasChildren ? (
          <button onClick={() => toggleExpand(reseller.id)} className="focus:outline-none">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-slate-600" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-600" />
            )}
          </button>
        ) : (
          <div className="w-4" />
        )}
        
        {/* Icon */}
        <span className="text-xl">
          {level === 0 ? '🌟' : level === 1 ? '📦' : '📁'}
        </span>
        
        {/* Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-900">{reseller.name}</span>
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
              L{reseller.level || 0}
            </span>
            {reseller.custom_domain && (
              <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
                {reseller.custom_domain}
              </span>
            )}
            {hasChildren && (
              <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                {reseller.children.length} sub
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">{reseller.email}</p>
        </div>
        
        {/* Actions */}
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTransferModal({ open: true, reseller, new_parent_id: null })}
            className="h-7 px-2"
          >
            <ArrowRightLeft className="w-3 h-3" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDeleteReseller(reseller.id)}
            className="h-7 px-2 text-red-600 hover:bg-red-50"
          >
            <Trash2 className="w-3 h-3" />
          </Button>
        </div>
      </div>
      
      {/* Children */}
      {isExpanded && hasChildren && (
        <div>
          {reseller.children.map(child => (
            <ResellerTreeNode
              key={child.id}
              reseller={child}
              level={level + 1}
              expandedResellers={expandedResellers}
              toggleExpand={toggleExpand}
              handleDeleteReseller={handleDeleteReseller}
              setTransferModal={setTransferModal}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ResellerTreeNode;
