import { EntityType, BranchType } from '@/types/ontology/entity-graph';

export const ENTITY_COLORS: Record<EntityType, string> = {
  data_source: '#6b7280',
  dataset: '#0E4F70',
  analysis: '#004806',
  pipeline: '#840B08',
  model_instantiated: '#491A32',
} as const;

export interface EntityColorClasses {
  bg: string;
  bgHover: string;
  border: string;
  borderHover: string;
  text: string;
  icon: string;
  buttonBg: string;
  buttonHover: string;
  plusBg: string;
  plusBorder: string;
}

export function getEntityColorClasses(type: EntityType): EntityColorClasses {
  switch (type) {
    case 'dataset':
      return {
        bg: 'bg-[#0E4F70]/10',
        bgHover: 'hover:bg-[#0E4F70]/20',
        border: 'border border-[#0E4F70]',
        borderHover: 'hover:border-[#0E4F70]',
        text: 'text-gray-700',
        icon: 'text-[#0E4F70]',
        buttonBg: 'bg-[#0E4F70]/10',
        buttonHover: 'hover:bg-[#0E4F70]/30',
        plusBg: 'bg-[#0E4F70]',
        plusBorder: 'border-[#0E4F70]/50',
      };
    case 'data_source':
      return {
        bg: 'bg-[#6b7280]/10',
        bgHover: 'hover:bg-[#6b7280]/20',
        border: 'border border-gray-600',
        borderHover: 'hover:border-[#6b7280]',
        text: 'text-gray-700',
        icon: 'text-gray-600',
        buttonBg: 'bg-[#6b7280]/10',
        buttonHover: 'hover:bg-[#6b7280]/20',
        plusBg: 'bg-gray-600',
        plusBorder: 'border-gray-300',
      };
    case 'analysis':
      return {
        bg: 'bg-[#004806]/10',
        bgHover: 'hover:bg-[#004806]/20',
        border: 'border border-[#004806]',
        borderHover: 'hover:border-[#004806]',
        text: 'text-gray-700',
        icon: 'text-[#004806]',
        buttonBg: 'bg-[#004806]/10',
        buttonHover: 'hover:bg-[#004806]/30',
        plusBg: 'bg-[#004806]',
        plusBorder: 'border-[#004806]/50',
      };
    case 'pipeline':
      return {
        bg: 'bg-[#840B08]/10',
        bgHover: 'hover:bg-[#840B08]/20',
        border: 'border border-[#840B08]',
        borderHover: 'hover:border-[#840B08]',
        text: 'text-gray-700',
        icon: 'text-[#840B08]',
        buttonBg: 'bg-[#840B08]/10',
        buttonHover: 'hover:bg-[#840B08]/30',
        plusBg: 'bg-[#840B08]',
        plusBorder: 'border-[#840B08]/50',
      };
    case 'model_instantiated':
      return {
        bg: 'bg-[#491A32]/10',
        bgHover: 'hover:bg-[#491A32]/20',
        border: 'border border-[#491A32]',
        borderHover: 'hover:border-[#491A32]',
        text: 'text-gray-700',
        icon: 'text-[#491A32]',
        buttonBg: 'bg-[#491A32]/10',
        buttonHover: 'hover:bg-[#491A32]/30',
        plusBg: 'bg-[#491A32]',
        plusBorder: 'border-[#491A32]/50',
      };
  }
}

export interface BranchColorClasses {
  stroke: string;
  iconBg: string;
  iconBorder: string;
  iconColor: string;
  labelColor: string;
  hoverBg: string;
}

export function getBranchColorClasses(branchType: BranchType): BranchColorClasses {
  switch (branchType) {
    case 'dataset':
      return {
        stroke: '#0E4F70',
        iconBg: 'bg-[#0E4F70]/10',
        iconBorder: 'border-[#0E4F70]/30',
        iconColor: 'text-[#0E4F70]',
        labelColor: 'text-[#0E4F70]',
        hoverBg: 'hover:bg-[#0E4F70]/10',
      };
    case 'data_source':
      return {
        stroke: '#6b7280',
        iconBg: 'bg-[#6b7280]/10',
        iconBorder: 'border-[#6b7280]/30',
        iconColor: 'text-gray-600',
        labelColor: 'text-gray-600',
        hoverBg: 'hover:bg-[#6b7280]/10',
      };
    case 'analysis':
      return {
        stroke: '#004806',
        iconBg: 'bg-[#004806]/10',
        iconBorder: 'border-[#004806]/30',
        iconColor: 'text-[#004806]',
        labelColor: 'text-[#004806]',
        hoverBg: 'hover:bg-[#004806]/10',
      };
    case 'pipeline':
      return {
        stroke: '#840B08',
        iconBg: 'bg-[#840B08]/10',
        iconBorder: 'border-[#840B08]/30',
        iconColor: 'text-[#840B08]',
        labelColor: 'text-[#840B08]',
        hoverBg: 'hover:bg-[#840B08]/10',
      };
    case 'model_instantiated':
      return {
        stroke: '#491A32',
        iconBg: 'bg-[#491A32]/10',
        iconBorder: 'border-[#491A32]/30',
        iconColor: 'text-[#491A32]',
        labelColor: 'text-[#491A32]',
        hoverBg: 'hover:bg-[#491A32]/10',
      };
    case 'mixed':
    default:
      return {
        stroke: '#000000',
        iconBg: 'bg-gray-900/10',
        iconBorder: 'border-gray-900/30',
        iconColor: 'text-gray-900',
        labelColor: 'text-gray-900',
        hoverBg: 'hover:bg-gray-900/10',
      };
  }
}

export function getEntityMiniClasses(type: EntityType) {
  switch (type) {
    case 'dataset':
      return {
        bg: 'bg-[#0E4F70]/20',
        text: 'text-[#0E4F70]',
        hover: 'hover:text-gray-400',
      };
    case 'data_source':
      return {
        bg: 'bg-gray-200',
        text: 'text-gray-600',
        hover: 'hover:text-gray-400',
      };
    case 'analysis':
      return {
        bg: 'bg-[#004806]/20',
        text: 'text-[#004806]',
        hover: 'hover:text-gray-400',
      };
    case 'pipeline':
      return {
        bg: 'bg-[#840B08]/20',
        text: 'text-[#840B08]',
        hover: 'hover:text-gray-400',
      };
    case 'model_instantiated':
      return {
        bg: 'bg-[#491A32]/20',
        text: 'text-[#491A32]',
        hover: 'hover:text-gray-400',
      };
  }
}

export interface EntityBoxClasses {
  border: string;
  borderHover: string;
  bg: string;
  bgHover: string;
  bgInContext: string;
  ring: string;
  iconBg: string;
  iconBorder: string;
  iconColor: string;
  labelColor: string;
}

export function getEntityBoxClasses(type: EntityType): EntityBoxClasses {
  switch (type) {
    case 'dataset':
      return {
        border: 'border-[#0E4F70]',
        borderHover: 'hover:border-[#0E4F70]',
        bg: 'bg-[#0E4F70]/10',
        bgHover: 'hover:bg-[#0E4F70]/10',
        bgInContext: 'bg-[#0E4F70]/10',
        ring: 'ring-2 ring-[#0E4F70]/30',
        iconBg: 'bg-[#0E4F70]/10',
        iconBorder: 'border-[#0E4F70]/30',
        iconColor: 'text-[#0E4F70]',
        labelColor: 'text-[#0E4F70]',
      };
    case 'data_source':
      return {
        border: 'border-gray-600',
        borderHover: 'hover:border-[#6b7280]',
        bg: 'bg-[#6b7280]/20',
        bgHover: 'hover:bg-[#6b7280]/10',
        bgInContext: 'bg-[#6b7280]/20',
        ring: 'ring-4 ring-[#6b7280]/50',
        iconBg: 'bg-gray-500/10',
        iconBorder: 'border-gray-400/30',
        iconColor: 'text-gray-600',
        labelColor: 'text-gray-600',
      };
    case 'analysis':
      return {
        border: 'border-[#004806]',
        borderHover: 'hover:border-[#004806]',
        bg: 'bg-[#004806]/10',
        bgHover: 'hover:bg-[#004806]/10',
        bgInContext: 'bg-[#004806]/10',
        ring: 'ring-2 ring-[#004806]/30',
        iconBg: 'bg-[#004806]/10',
        iconBorder: 'border-[#004806]/30',
        iconColor: 'text-[#004806]',
        labelColor: 'text-[#004806]',
      };
    case 'pipeline':
      return {
        border: 'border-[#840B08]',
        borderHover: 'hover:border-[#840B08]',
        bg: 'bg-[#840B08]/10',
        bgHover: 'hover:bg-[#840B08]/10',
        bgInContext: 'bg-[#840B08]/10',
        ring: 'ring-2 ring-[#840B08]/30',
        iconBg: 'bg-[#840B08]/10',
        iconBorder: 'border-[#840B08]/30',
        iconColor: 'text-[#840B08]',
        labelColor: 'text-[#840B08]',
      };
    case 'model_instantiated':
      return {
        border: 'border-[#491A32]',
        borderHover: 'hover:border-[#491A32]',
        bg: 'bg-[#491A32]/10',
        bgHover: 'hover:bg-[#491A32]/10',
        bgInContext: 'bg-[#491A32]/10',
        ring: 'ring-2 ring-[#491A32]/30',
        iconBg: 'bg-[#491A32]/10',
        iconBorder: 'border-[#491A32]/30',
        iconColor: 'text-[#491A32]',
        labelColor: 'text-[#491A32]',
      };
  }
}
