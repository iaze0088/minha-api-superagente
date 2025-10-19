import { Card } from '@/components/ui/card';
import { GitBranch } from 'lucide-react';
import ResellerTreeNode from './ResellerTreeNode';

const ResellerTree = ({ hierarchy, expandedResellers, toggleExpand, handleDeleteReseller, setTransferModal }) => (
  <Card className="p-6">
    <h4 className="font-semibold mb-4 flex items-center gap-2">
      <GitBranch className="w-5 h-5" />
      Hierarquia de Revendas
    </h4>
    
    {hierarchy.hierarchy && hierarchy.hierarchy.length > 0 ? (
      <div className="space-y-2">
        {hierarchy.hierarchy.map(reseller => (
          <ResellerTreeNode 
            key={reseller.id} 
            reseller={reseller} 
            level={0}
            expandedResellers={expandedResellers}
            toggleExpand={toggleExpand}
            handleDeleteReseller={handleDeleteReseller}
            setTransferModal={setTransferModal}
          />
        ))}
      </div>
    ) : (
      <p className="text-slate-500 text-center py-8">Nenhuma revenda na hierarquia</p>
    )}
  </Card>
);

export default ResellerTree;
